import { useCallback, useEffect, useRef, useState } from 'react'
import type { IChartApi, ISeriesApi, MouseEventParams, SeriesType } from 'lightweight-charts'
import { usarDibujos } from '../../../hooks/usarDibujos'
import { crearRenderizadorDibujos, type RenderizadorDibujos } from './renderizadorDibujos'
import BarraHerramientas from './BarraHerramientas'
import type { TipoHerramienta, PuntoDibujo } from './tipos'

interface Props {
  ticker: string
  obtenerChart: () => IChartApi | null
  obtenerSerie: () => ISeriesApi<SeriesType> | null
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
  const [herramienta, setHerramienta] = useState<TipoHerramienta>(null)
  const renderizador = useRef<RenderizadorDibujos | null>(null)
  const herramientaRef = useRef(herramienta)
  herramientaRef.current = herramienta
  const agregarRef = useRef(agregar)
  agregarRef.current = agregar
  const primerPunto = useRef<PuntoDibujo | null>(null)
  const seleccionado = useRef<number | null>(null)

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
    if (seleccionado.current != null && !dibujos.some((d) => d.id === seleccionado.current)) {
      seleccionado.current = null
    }
  }, [dibujos])

  // Al activar una herramienta, soltar la selección y resetear el primer punto
  useEffect(() => {
    primerPunto.current = null
    renderizador.current?.limpiarPrevisualizacion()
    if (herramienta) {
      seleccionado.current = null
      renderizador.current?.seleccionar(null)
    }
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
      seleccionado.current = null
    }
    window.addEventListener('keydown', alTecla)
    return () => window.removeEventListener('keydown', alTecla)
  }, [eliminar])

  useEffect(() => {
    const chart = obtenerChart()
    if (!chart) return

    const alClick = (params: MouseEventParams) => {
      const tipo = herramientaRef.current

      // Sin herramienta activa: el click selecciona el dibujo tocado (o lo deselecciona)
      if (!tipo) {
        if (!params.point) return
        const id = renderizador.current?.dibujoEn(params.point.x, params.point.y) ?? null
        seleccionado.current = id
        renderizador.current?.seleccionar(id)
        return
      }

      const serie = obtenerSerie()
      if (!serie) return

      if (tipo === 'horizontal') {
        const punto = extraerPunto(params, serie)
        if (!punto) return
        agregarRef.current('horizontal', { precio: punto.precio })
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
      agregarRef.current(tipo, { p1, p2: punto })
      setHerramienta(null)
    }

    // Mientras hay un primer punto pendiente, la línea sigue al mouse.
    // Se usa la posición en píxeles (params.point), continua y fluida, en vez
    // de params.time, que se imanta al centro de cada vela.
    const alMover = (params: MouseEventParams) => {
      const tipo = herramientaRef.current
      if (!tipo || tipo === 'horizontal') return
      const p1 = primerPunto.current
      if (!p1 || !params.point) return
      renderizador.current?.previsualizar(tipo, p1, params.point.x, params.point.y)
    }

    chart.subscribeClick(alClick)
    chart.subscribeCrosshairMove(alMover)
    return () => {
      chart.unsubscribeClick(alClick)
      chart.unsubscribeCrosshairMove(alMover)
    }
  }, [obtenerChart, obtenerSerie])

  const borrarTodo = useCallback(async () => {
    for (const d of dibujos) {
      await eliminar(d.id)
    }
  }, [dibujos, eliminar])

  return (
    <BarraHerramientas
      activa={herramienta}
      alSeleccionar={setHerramienta}
      alBorrarTodo={borrarTodo}
    />
  )
}

export default CapaDibujos
