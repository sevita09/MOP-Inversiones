import { useEffect, useRef } from 'react'
import { createChart } from 'lightweight-charts'
import type {
  CandlestickData,
  IChartApi,
  ISeriesApi,
  UTCTimestamp,
} from 'lightweight-charts'
import type { Moneda, Temporalidad, Vela } from '../../api/tipos'
import { usarVelas } from '../../hooks/usarVelas'
import { OPCIONES_GRAFICO, OPCIONES_VELAS } from './configGrafico'

function aDatosVelas(velas: Vela[]): CandlestickData[] {
  return velas.map((vela) => ({
    time: vela.ts as UTCTimestamp,
    open: vela.apertura,
    high: vela.maximo,
    low: vela.minimo,
    close: vela.cierre,
  }))
}

interface Props {
  ticker: string
  temporalidad: Temporalidad
  moneda: Moneda
}

function PanelPrecio({ ticker, temporalidad, moneda }: Props) {
  const contenedor = useRef<HTMLDivElement>(null)
  const grafico = useRef<IChartApi | null>(null)
  const serie = useRef<ISeriesApi<'Candlestick'> | null>(null)
  const { velas, cargando, error } = usarVelas(ticker, temporalidad, moneda)

  // Crear el gráfico una sola vez; autoSize lo mantiene del tamaño del contenedor
  useEffect(() => {
    if (!contenedor.current) return
    const chart = createChart(contenedor.current, {
      ...OPCIONES_GRAFICO,
      autoSize: true,
    })
    serie.current = chart.addCandlestickSeries(OPCIONES_VELAS)
    grafico.current = chart

    return () => {
      chart.remove()
      grafico.current = null
      serie.current = null
    }
  }, [])

  // Volcar las velas cuando cambian
  useEffect(() => {
    if (!serie.current) return
    serie.current.setData(aDatosVelas(velas))
    grafico.current?.timeScale().fitContent()
  }, [velas])

  return (
    <div className="panel-precio">
      <div ref={contenedor} className="grafico" />
      {cargando && <div className="grafico-aviso">Cargando…</div>}
      {error && <div className="grafico-aviso grafico-error">{error}</div>}
    </div>
  )
}

export default PanelPrecio
