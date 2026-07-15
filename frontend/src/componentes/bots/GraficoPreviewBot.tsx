import { useEffect, useRef } from 'react'
import { createChart } from 'lightweight-charts'
import type {
  CandlestickData,
  IChartApi,
  ISeriesApi,
  SeriesMarker,
  UTCTimestamp,
} from 'lightweight-charts'
import type { Moneda, ReglasBot, TemporalidadBot } from '../../api/tipos'
import { COLORES, OPCIONES_GRAFICO, OPCIONES_VELAS } from '../grafico/configGrafico'
import { usarVelas } from '../../hooks/usarVelas'
import { usarPreviewBot } from '../../hooks/usarPreviewBot'
import './GraficoPreviewBot.css'

interface Props {
  ticker: string
  temporalidad: TemporalidadBot
  moneda: Moneda
  reglas: ReglasBot
}

/** Chart compacto del editor de bots: las velas del ticker con las señales de
 *  la vista previa marcadas encima (▲ entrada verde, ▼ salida roja). */
function GraficoPreviewBot({ ticker, temporalidad, moneda, reglas }: Props) {
  const contenedor = useRef<HTMLDivElement>(null)
  const chartRef = useRef<IChartApi | null>(null)
  const serieRef = useRef<ISeriesApi<'Candlestick'> | null>(null)
  const { velas, cargando } = usarVelas(ticker, temporalidad, moneda)
  const senales = usarPreviewBot(ticker, temporalidad, moneda, reglas)

  useEffect(() => {
    if (!contenedor.current) return
    const chart = createChart(contenedor.current, {
      ...OPCIONES_GRAFICO,
      autoSize: true,
      timeScale: { ...OPCIONES_GRAFICO.timeScale, timeVisible: false },
    })
    chartRef.current = chart
    serieRef.current = chart.addCandlestickSeries(OPCIONES_VELAS)
    return () => {
      chartRef.current = null
      serieRef.current = null
      chart.remove()
    }
  }, [])

  useEffect(() => {
    if (!serieRef.current) return
    const datos: CandlestickData[] = velas.map((vela) => ({
      time: vela.ts as UTCTimestamp,
      open: vela.apertura,
      high: vela.maximo,
      low: vela.minimo,
      close: vela.cierre,
    }))
    serieRef.current.setData(datos)
    chartRef.current?.timeScale().fitContent()
  }, [velas])

  useEffect(() => {
    if (!serieRef.current) return
    const marcadores: SeriesMarker<UTCTimestamp>[] = [
      ...senales.ts_entrada.map((ts) => ({
        time: ts as UTCTimestamp,
        position: 'belowBar' as const,
        color: COLORES.verde,
        shape: 'arrowUp' as const,
      })),
      ...senales.ts_salida.map((ts) => ({
        time: ts as UTCTimestamp,
        position: 'aboveBar' as const,
        color: COLORES.rojo,
        shape: 'arrowDown' as const,
      })),
    ].sort((a, b) => a.time - b.time)
    serieRef.current.setMarkers(marcadores)
  }, [senales, velas])

  return (
    <div className="preview-bot">
      <div className="cabecera-preview-bot">
        <span>Vista previa — {ticker}</span>
        <span className="conteo-senales">
          <span className="senal-entrada">▲ {senales.ts_entrada.length}</span>
          {' · '}
          <span className="senal-salida">▼ {senales.ts_salida.length}</span>
        </span>
      </div>
      <div ref={contenedor} className="area-preview-bot">
        {cargando && <div className="cargando-preview">Cargando…</div>}
      </div>
    </div>
  )
}

export default GraficoPreviewBot
