import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import type { IChartApi, ISeriesApi, MouseEventParams, SeriesType } from 'lightweight-charts'
import type { Moneda } from '../../../api/tipos'
import { usarDibujos } from '../../../hooks/usarDibujos'
import { usarEstadoPersistente } from '../../../hooks/usarEstadoPersistente'
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
import type { TipoHerramienta, PuntoDibujo, PuntoMedicion } from './tipos'

interface Props {
  ticker: string
  moneda: Moneda
  obtenerChart: () => IChartApi | null
  obtenerSerie: () => ISeriesApi<SeriesType> | null
  precioIman: (ts: number, yPixel: number) => number | null
}

const TITULO_HERRAMIENTA: Record<string, string> = {
  horizontal: 'Línea horizontal',
  tendencia: 'Tendencia',
  fibonacci: 'Fibonacci',
  medicion: 'Medición',
}

// Imán: si está activo y el cursor está sobre una vela, engancha el precio a su
// apertura o cierre (el más cercano al cursor). Devuelve el precio a usar.
type Iman = ((ts: number, yPixel: number) => number | null) | null

function precioConIman(params: MouseEventParams, precio: number, iman: Iman): number {
  if (!iman || params.time == null || !params.point) return precio
  return iman(params.time as number, params.point.y) ?? precio
}

function extraerPunto(
  params: MouseEventParams,
  serie: ISeriesApi<SeriesType>,
  iman: Iman,
): PuntoDibujo | null {
  if (!params.point || !params.time) return null
  const bruto = serie.coordinateToPrice(params.point.y)
  if (bruto == null || !isFinite(bruto)) return null
  const precio = precioConIman(params, bruto, iman)
  return { ts: params.time as number, precio: Math.round(precio * 100) / 100 }
}

// La medición es una regla: ancla en coordenada lógica fraccional (cualquier punto,
// no imantada al centro de una vela). No necesita `params.time` (salvo con imán).
function extraerPuntoLibre(
  params: MouseEventParams,
  chart: IChartApi,
  serie: ISeriesApi<SeriesType>,
  iman: Iman,
): PuntoMedicion | null {
  if (!params.point) return null
  const logical = chart.timeScale().coordinateToLogical(params.point.x)
  const bruto = serie.coordinateToPrice(params.point.y)
  if (logical == null || bruto == null || !isFinite(bruto)) return null
  const precio = precioConIman(params, bruto, iman)
  return { logical, precio: Math.round(precio * 100) / 100 }
}

function CapaDibujos({ ticker, moneda, obtenerChart, obtenerSerie, precioIman }: Props) {
  const { dibujos, agregar, actualizar, eliminar } = usarDibujos(ticker)
  const { estiloDe, guardar, volver, overrideDe } = usarEstilos()
  const [herramienta, setHerramienta] = useState<TipoHerramienta>(null)
  const [iman, setIman] = usarEstadoPersistente('mop.iman', false)
  const [idSeleccionado, setIdSeleccionado] = useState<number | null>(null)
  const [configId, setConfigId] = useState<number | null>(null)
  const renderizador = useRef<RenderizadorDibujos | null>(null)
  const herramientaRef = useRef(herramienta)
  const agregarRef = useRef(agregar)
  const estiloDeRef = useRef(estiloDe)
  const monedaRef = useRef(moneda)
  // Imán efectivo para los handlers: la función de enganche si está activo, o null
  const imanRef = useRef<Iman>(null)
  const primerPunto = useRef<PuntoMedicion | null>(null)
  const seleccionado = useRef<number | null>(null)

  // Un dibujo se ve solo en la moneda en que se creó (un precio en ARS no tiene
  // sentido en la vista USD). Los viejos sin moneda registrada se muestran siempre.
  const visibles = useMemo(
    () => dibujos.filter((d) => d.datos.moneda == null || d.datos.moneda === moneda),
    [dibujos, moneda],
  )

  // Mantener los refs con el último valor sin reasignarlos durante el render
  useEffect(() => {
    herramientaRef.current = herramienta
    agregarRef.current = agregar
    estiloDeRef.current = estiloDe
    monedaRef.current = moneda
    imanRef.current = iman ? precioIman : null
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
    renderizador.current?.sincronizar(visibles)
  }, [visibles])

  // Si el dibujo seleccionado se borró o dejó de verse (cambió la moneda), la
  // selección queda obsoleta: se deriva su validez para la tuerca en vez de setear
  // estado en un effect.
  const seleccionValida = idSeleccionado != null && visibles.some((d) => d.id === idSeleccionado)

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
        const punto = extraerPunto(params, serie, imanRef.current)
        if (!punto) return
        agregarRef.current('horizontal', {
          precio: punto.precio,
          estilo: estiloNuevo('horizontal'),
          moneda: monedaRef.current,
        })
        setHerramienta(null)
        return
      }

      // Herramientas de dos puntos: tendencia y fibonacci se imantan a la vela;
      // la medición ancla libre (regla) en coordenada lógica fraccional. El imán
      // (si está activo) engancha el precio a la apertura/cierre en cualquiera de ellas.
      const punto =
        tipo === 'medicion'
          ? extraerPuntoLibre(params, chart, serie, imanRef.current)
          : extraerPunto(params, serie, imanRef.current)
      if (!punto) return

      if (!primerPunto.current) {
        primerPunto.current = punto
        return
      }

      const p1 = primerPunto.current
      primerPunto.current = null
      renderizador.current?.limpiarPrevisualizacion()
      agregarRef.current(tipo, { p1, p2: punto, estilo: estiloNuevo(tipo), moneda: monedaRef.current })
      setHerramienta(null)
    }

    // Mientras hay un primer punto pendiente, la línea sigue al mouse (en píxeles).
    // Con el imán activo, el extremo se pega a la apertura/cierre de la vela.
    const alMover = (params: MouseEventParams) => {
      const tipo = herramientaRef.current
      if (!tipo || tipo === 'horizontal') return
      const p1 = primerPunto.current
      if (!p1 || !params.point) return
      let y = params.point.y
      if (imanRef.current && params.time != null) {
        const precioImanado = imanRef.current(params.time as number, params.point.y)
        const yImanado = precioImanado != null ? obtenerSerie()?.priceToCoordinate(precioImanado) : null
        if (yImanado != null) y = yImanado
      }
      renderizador.current?.previsualizar(tipo, p1, params.point.x, y, estiloNuevo(tipo))
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

  // "Borrar todo" borra solo lo visible (los de la moneda actual)
  const borrarTodo = useCallback(async () => {
    for (const d of visibles) {
      await eliminar(d.id)
    }
  }, [visibles, eliminar])

  const dibujoConfig = configId != null ? visibles.find((d) => d.id === configId) ?? null : null

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
        iman={iman}
        alAlternarIman={() => setIman(!iman)}
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
