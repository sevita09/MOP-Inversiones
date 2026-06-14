import { useEffect, useMemo, useRef, useState } from 'react'
import { createChart } from 'lightweight-charts'
import type {
  CandlestickData,
  IChartApi,
  ISeriesApi,
  LineData,
  MouseEventParams,
  SeriesType,
  UTCTimestamp,
} from 'lightweight-charts'
import type { Moneda, Temporalidad, TipoGrafico, Vela } from '../../api/tipos'
import { usarVelas } from '../../hooks/usarVelas'
import {
  OPCIONES_AREA,
  OPCIONES_GRAFICO,
  OPCIONES_LINEA,
  OPCIONES_VELAS,
} from './configGrafico'
import LeyendaOHLC from './LeyendaOHLC'
import './PanelPrecio.css'

function datosVelas(velas: Vela[]): CandlestickData[] {
  return velas.map((vela) => ({
    time: vela.ts as UTCTimestamp,
    open: vela.apertura,
    high: vela.maximo,
    low: vela.minimo,
    close: vela.cierre,
  }))
}

function datosLinea(velas: Vela[]): LineData[] {
  return velas.map((vela) => ({ time: vela.ts as UTCTimestamp, value: vela.cierre }))
}

function crearSerie(chart: IChartApi, tipo: TipoGrafico): ISeriesApi<SeriesType> {
  if (tipo === 'linea') return chart.addLineSeries(OPCIONES_LINEA)
  if (tipo === 'area') return chart.addAreaSeries(OPCIONES_AREA)
  return chart.addCandlestickSeries(OPCIONES_VELAS)
}

function volcarDatos(serie: ISeriesApi<SeriesType>, tipo: TipoGrafico, velas: Vela[]) {
  serie.setData(tipo === 'velas' ? datosVelas(velas) : datosLinea(velas))
}

interface Props {
  ticker: string
  temporalidad: Temporalidad
  moneda: Moneda
  tipo: TipoGrafico
}

function PanelPrecio({ ticker, temporalidad, moneda, tipo }: Props) {
  const contenedor = useRef<HTMLDivElement>(null)
  const grafico = useRef<IChartApi | null>(null)
  const serie = useRef<ISeriesApi<SeriesType> | null>(null)
  const { velas, cargando, error } = usarVelas(ticker, temporalidad, moneda)
  // Índice de la vela bajo el crosshair; null = ninguna (se muestra la última)
  const [indiceActivo, setIndiceActivo] = useState<number | null>(null)

  const indicePorTs = useMemo(() => {
    const mapa = new Map<number, number>()
    velas.forEach((vela, indice) => mapa.set(vela.ts, indice))
    return mapa
  }, [velas])
  // El handler del crosshair se crea una sola vez; el ref le da siempre el mapa actual
  const indicePorTsRef = useRef(indicePorTs)
  indicePorTsRef.current = indicePorTs
  const velasRef = useRef(velas)
  velasRef.current = velas

  // Crear el gráfico una sola vez; autoSize lo mantiene del tamaño del contenedor
  useEffect(() => {
    if (!contenedor.current) return
    const chart = createChart(contenedor.current, { ...OPCIONES_GRAFICO, autoSize: true })
    grafico.current = chart

    const alMover = (parametros: MouseEventParams) => {
      const ts = parametros.time as number | undefined
      setIndiceActivo(ts != null ? indicePorTsRef.current.get(ts) ?? null : null)
    }
    chart.subscribeCrosshairMove(alMover)

    return () => {
      chart.unsubscribeCrosshairMove(alMover)
      chart.remove()
      grafico.current = null
      serie.current = null
    }
  }, [])

  // Crear/recrear la serie al cambiar el tipo de gráfico
  useEffect(() => {
    const chart = grafico.current
    if (!chart) return
    const s = crearSerie(chart, tipo)
    serie.current = s
    volcarDatos(s, tipo, velasRef.current)
    return () => {
      // Si el chart ya fue destruido, sus series se liberaron solas: ignorar
      try {
        chart.removeSeries(s)
      } catch {
        /* chart disposed */
      }
      serie.current = null
    }
  }, [tipo])

  // Volcar las velas cuando cambian. El rango temporal solo se reencuadra al
  // cambiar de ticker o temporalidad, no al togglear moneda ni refrescar.
  const claveVista = `${ticker}-${temporalidad}`
  const claveAnterior = useRef('')
  useEffect(() => {
    if (!serie.current) return
    volcarDatos(serie.current, tipo, velas)
    if (velas.length > 0 && claveAnterior.current !== claveVista) {
      grafico.current?.timeScale().fitContent()
      claveAnterior.current = claveVista
    }
  }, [velas, claveVista, tipo])

  const indiceMostrado = indiceActivo ?? velas.length - 1
  const velaMostrada = velas[indiceMostrado] ?? null
  const velaPrevia = indiceMostrado > 0 ? velas[indiceMostrado - 1] : null
  const hayVelas = velas.length > 0
  const sinDatos = !cargando && !error && !hayVelas

  return (
    <div className="panel-precio">
      {velaMostrada && <LeyendaOHLC vela={velaMostrada} velaPrevia={velaPrevia} />}
      <div ref={contenedor} className="grafico" />
      {cargando && !hayVelas && (
        <div className="grafico-estado">
          <span className="spinner" />
          Cargando {ticker}…
        </div>
      )}
      {error && !hayVelas && (
        <div className="grafico-estado grafico-estado-error">
          No se pudieron cargar los datos
          <span className="grafico-estado-detalle">{error}</span>
        </div>
      )}
      {error && hayVelas && (
        <div className="grafico-banner-error">Sin conexión — mostrando datos previos</div>
      )}
      {sinDatos && (
        <div className="grafico-estado">Sin datos para {ticker} en {temporalidad}</div>
      )}
    </div>
  )
}

export default PanelPrecio
