import { useCallback, useEffect, useRef, useState } from 'react'
import type { IChartApi, ISeriesApi, MouseEventParams, SeriesType } from 'lightweight-charts'
import { usarDibujos } from '../../../hooks/usarDibujos'
import { usarEstilos, type Estilo } from '../../../contextos/EstilosContext'
import { crearRenderizadorDibujos, type RenderizadorDibujos } from './renderizadorDibujos'
import BarraHerramientas from './BarraHerramientas'
import DialogoEstiloDibujo from './DialogoEstiloDibujo'
import {
  RECOMENDADO_DIBUJO,
  estiloDeDibujo,
  camposDibujo,
  idHerramienta,
} from './estiloDibujo'
import type { TipoHerramienta, PuntoDibujo } from './tipos'

interface Props {
  ticker: string
  obtenerChart: () => IChartApi | null
  obtenerSerie: () => ISeriesApi<SeriesType> | null
}

const TITULO_HERRAMIENTA: Record<string, string> = {
  horizontal: 'Línea horizontal',
  tendencia: 'Tendencia',
  fibonacci: 'Fibonacci',
  medicion: 'Medición',
}

function extraerPunto(
  params: MouseEventParams,
  serie: ISeriesApi<SeriesType>,
): PuntoDibujo | null {
  if (!params.point || !params.time) return null
  const precio = serie.coordinateToPrice(params.point.y)
  if (precio == null || !isFinite(precio)) return null
  return { ts: params.time as number, precio: Math.round(precio * 100) / 100 }
}

function CapaDibujos({ ticker, obtenerChart, obtenerSerie }: Props) {
  const { dibujos, agregar, actualizar, eliminar } = usarDibujos(ticker)
  const { estiloDe, guardar, volver, overrideDe } = usarEstilos()
  const [herramienta, setHerramienta] = useState<TipoHerramienta>(null)
  const [idSeleccionado, setIdSeleccionado] = useState<number | null>(null)
  const [configId, setConfigId] = useState<number | null>(null)
  const renderizador = useRef<RenderizadorDibujos | null>(null)
  const herramientaRef = useRef(herramienta)
  const agregarRef = useRef(agregar)
  const estiloDeRef = useRef(estiloDe)
  const primerPunto = useRef<PuntoDibujo | null>(null)
  const seleccionado = useRef<number | null>(null)

  // Mantener los refs con el último valor sin reasignarlos durante el render
  useEffect(() => {
    herramientaRef.current = herramienta
    agregarRef.current = agregar
    estiloDeRef.current = estiloDe
  })

  // Seleccionar un dibujo: ref (para los handlers) + estado (para mostrar la tuerca)
  const seleccionar = useCallback((id: number | null) => {
    seleccionado.current = id
    setIdSeleccionado(id)
    renderizador.current?.seleccionar(id)
  }, [])

  // Estilo con el que nace un dibujo nuevo: el default de esa herramienta
  const estiloNuevo = useCallback(
    (tipo: string): Estilo => estiloDeRef.current(idHerramienta(tipo), RECOMENDADO_DIBUJO),
    [],
  )

  // Activar una herramienta suelta la selección (en el handler, no en un effect)
  const activarHerramienta = useCallback(
    (tipo: TipoHerramienta) => {
      setHerramienta(tipo)
      if (tipo) seleccionar(null)
    },
    [seleccionar],
  )

  useEffect(() => {
    const chart = obtenerChart()
    const serie = obtenerSerie()
    if (!chart || !serie) return
    const r = crearRenderizadorDibujos(chart, serie, actualizar, eliminar)
    renderizador.current = r
    return () => {
      r.destruir()
      renderizador.current = null
    }
  }, [obtenerChart, obtenerSerie, actualizar, eliminar])

  useEffect(() => {
    renderizador.current?.sincronizar(dibujos)
  }, [dibujos])

  // Si el dibujo seleccionado se borró (p.ej. "borrar todo"), la selección queda
  // obsoleta: se deriva su validez para la tuerca en vez de setear estado en un effect.
  const seleccionValida = idSeleccionado != null && dibujos.some((d) => d.id === idSeleccionado)

  // Al cambiar de herramienta, resetear el primer punto y la previsualización
  useEffect(() => {
    primerPunto.current = null
    renderizador.current?.limpiarPrevisualizacion()
  }, [herramienta])

  // Borrar el dibujo seleccionado con Supr / Backspace
  useEffect(() => {
    const alTecla = (e: KeyboardEvent) => {
      if (e.key !== 'Delete' && e.key !== 'Backspace') return
      const id = seleccionado.current
      if (id == null) return
      const t = e.target as HTMLElement | null
      if (t && (t.tagName === 'INPUT' || t.tagName === 'TEXTAREA' || t.isContentEditable)) return
      e.preventDefault()
      eliminar(id)
      seleccionar(null)
    }
    window.addEventListener('keydown', alTecla)
    return () => window.removeEventListener('keydown', alTecla)
  }, [eliminar, seleccionar])

  useEffect(() => {
    const chart = obtenerChart()
    if (!chart) return

    const alClick = (params: MouseEventParams) => {
      const tipo = herramientaRef.current

      // Sin herramienta activa: el click selecciona el dibujo tocado (o lo deselecciona)
      if (!tipo) {
        if (!params.point) return
        const id = renderizador.current?.dibujoEn(params.point.x, params.point.y) ?? null
        seleccionar(id)
        return
      }

      const serie = obtenerSerie()
      if (!serie) return

      if (tipo === 'horizontal') {
        const punto = extraerPunto(params, serie)
        if (!punto) return
        agregarRef.current('horizontal', { precio: punto.precio, estilo: estiloNuevo('horizontal') })
        setHerramienta(null)
        return
      }

      // Herramientas de dos puntos: tendencia, fibonacci, medicion
      const punto = extraerPunto(params, serie)
      if (!punto) return

      if (!primerPunto.current) {
        primerPunto.current = punto
        return
      }

      const p1 = primerPunto.current
      primerPunto.current = null
      renderizador.current?.limpiarPrevisualizacion()
      agregarRef.current(tipo, { p1, p2: punto, estilo: estiloNuevo(tipo) })
      setHerramienta(null)
    }

    // Mientras hay un primer punto pendiente, la línea sigue al mouse (en píxeles).
    const alMover = (params: MouseEventParams) => {
      const tipo = herramientaRef.current
      if (!tipo || tipo === 'horizontal') return
      const p1 = primerPunto.current
      if (!p1 || !params.point) return
      renderizador.current?.previsualizar(tipo, p1, params.point.x, params.point.y, estiloNuevo(tipo))
    }

    // Doble click sobre un dibujo: abre su configuración de estilo
    const alDobleClick = (params: MouseEventParams) => {
      if (!params.point) return
      const id = renderizador.current?.dibujoEn(params.point.x, params.point.y) ?? null
      if (id == null) return
      seleccionar(id)
      setConfigId(id)
    }

    chart.subscribeClick(alClick)
    chart.subscribeCrosshairMove(alMover)
    chart.subscribeDblClick(alDobleClick)
    return () => {
      chart.unsubscribeClick(alClick)
      chart.unsubscribeCrosshairMove(alMover)
      chart.unsubscribeDblClick(alDobleClick)
    }
  }, [obtenerChart, obtenerSerie, seleccionar, estiloNuevo])

  const borrarTodo = useCallback(async () => {
    for (const d of dibujos) {
      await eliminar(d.id)
    }
  }, [dibujos, eliminar])

  const dibujoConfig = configId != null ? dibujos.find((d) => d.id === configId) ?? null : null

  return (
    <>
      <BarraHerramientas
        activa={herramienta}
        alSeleccionar={activarHerramienta}
        alBorrarTodo={borrarTodo}
        haySeleccion={seleccionValida}
        alConfigurar={() => {
          if (idSeleccionado != null) setConfigId(idSeleccionado)
        }}
      />
      {dibujoConfig && (
        <DialogoEstiloDibujo
          titulo={`Estilo · ${TITULO_HERRAMIENTA[dibujoConfig.tipo] ?? dibujoConfig.tipo}`}
          campos={camposDibujo(dibujoConfig.tipo)}
          estilo={estiloDeDibujo(dibujoConfig.datos)}
          recomendado={RECOMENDADO_DIBUJO}
          hayOverride={
            Object.keys((dibujoConfig.datos.estilo as Estilo) ?? {}).length > 0 ||
            dibujoConfig.datos.color != null ||
            Object.keys(overrideDe(idHerramienta(dibujoConfig.tipo))).length > 0
          }
          alCambiar={(cambios) => {
            const estiloPrevio = (dibujoConfig.datos.estilo as Estilo) ?? {}
            actualizar(dibujoConfig.id, {
              ...dibujoConfig.datos,
              estilo: { ...estiloPrevio, ...cambios },
            })
            guardar(idHerramienta(dibujoConfig.tipo), cambios)
          }}
          alVolver={() => {
            const resto = { ...dibujoConfig.datos }
            delete resto.color
            delete resto.estilo
            actualizar(dibujoConfig.id, resto)
            volver(idHerramienta(dibujoConfig.tipo))
          }}
          alCerrar={() => setConfigId(null)}
        />
      )}
    </>
  )
}

export default CapaDibujos
