import { useEffect, useRef } from 'react'
import { createChart } from 'lightweight-charts'
import type {
  CandlestickData,
  IChartApi,
  ISeriesApi,
  SeriesMarker,
  UTCTimestamp,
} from 'lightweight-charts'
import type { Moneda, TemporalidadBot, TradeBacktest } from '../../api/tipos'
import { COLORES, OPCIONES_GRAFICO, OPCIONES_VELAS } from '../grafico/configGrafico'
import type { SincronizadorTiempo } from '../grafico/sincronizadorTiempo'
import { usarVelas } from '../../hooks/usarVelas'
import './GraficoTrades.css'

interface Props {
  ticker: string
  temporalidad: TemporalidadBot
  moneda: Moneda
  trades: TradeBacktest[]
  desde: number | null
  hasta: number | null
  sincronizador: SincronizadorTiempo
}

// La salida se pinta según por qué cerró (mismos colores que la tabla)
const COLOR_SALIDA: Record<string, string> = {
  stop: COLORES.rojo,
  trailing: '#d29922',
  take_profit: COLORES.verde,
  senal: '#58a6ff',
  fin: '#8b949e',
}

/** Velas del ticker con las operaciones del backtest marcadas encima. */
function GraficoTrades({
  ticker,
  temporalidad,
  moneda,
  trades,
  desde,
  hasta,
  sincronizador,
}: Props) {
  const contenedor = useRef<HTMLDivElement>(null)
  const chartRef = useRef<IChartApi | null>(null)
  const serieRef = useRef<ISeriesApi<'Candlestick'> | null>(null)
  const { velas, cargando } = usarVelas(ticker, temporalidad, moneda)

  useEffect(() => {
    if (!contenedor.current) return
    const chart = createChart(contenedor.current, {
      ...OPCIONES_GRAFICO,
      autoSize: true,
      timeScale: { ...OPCIONES_GRAFICO.timeScale, timeVisible: false },
    })
    chartRef.current = chart
    serieRef.current = chart.addCandlestickSeries(OPCIONES_VELAS)
    const liberar = sincronizador.registrar(chart)
    return () => {
      liberar()
      chartRef.current = null
      serieRef.current = null
      chart.remove()
    }
  }, [sincronizador])

  useEffect(() => {
    const chart = chartRef.current
    if (!serieRef.current || !chart) return
    // Solo las barras del rango del backtest: así ambos gráficos tienen los
    // mismos índices y el sincronizador (que trabaja por rango lógico) alinea
    const datos: CandlestickData[] = velas
      .filter((v) => (desde === null || v.ts >= desde) && (hasta === null || v.ts <= hasta))
      .map((vela) => ({
        time: vela.ts as UTCTimestamp,
        open: vela.apertura,
        high: vela.maximo,
        low: vela.minimo,
        close: vela.cierre,
      }))
    sincronizador.volcarYSincronizar(chart, () => {
      serieRef.current?.setData(datos)
    })
  }, [velas, desde, hasta, sincronizador])

  useEffect(() => {
    if (!serieRef.current) return
    const marcadores: SeriesMarker<UTCTimestamp>[] = []
    for (const trade of trades) {
      marcadores.push({
        time: trade.entrada_ts as UTCTimestamp,
        position: 'belowBar',
        color: COLORES.verde,
        shape: 'arrowUp',
        text: 'C',
      })
      marcadores.push({
        time: trade.salida_ts as UTCTimestamp,
        position: 'aboveBar',
        color: COLOR_SALIDA[trade.motivo] ?? COLORES.rojo,
        shape: 'arrowDown',
        text: `${trade.pnl_pct > 0 ? '+' : ''}${trade.pnl_pct.toFixed(0)}%`,
      })
    }
    marcadores.sort((a, b) => (a.time as number) - (b.time as number))
    serieRef.current.setMarkers(marcadores)
  }, [trades, velas])

  return (
    <div className="grafico-trades">
      <div className="leyenda-trades">
        <span className="marca-leyenda compra">▲ compra</span>
        <span className="marca-leyenda venta">▼ venta (color según motivo)</span>
      </div>
      <div ref={contenedor} className="area-trades">
        {cargando && <div className="cargando-trades">Cargando…</div>}
      </div>
    </div>
  )
}

export default GraficoTrades
