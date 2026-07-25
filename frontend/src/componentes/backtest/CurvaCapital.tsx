import { useEffect, useRef } from 'react'
import { createChart } from 'lightweight-charts'
import type { IChartApi, ISeriesApi, LineData, UTCTimestamp } from 'lightweight-charts'
import type { PuntoCurva } from '../../api/tipos'
import { COLORES, OPCIONES_GRAFICO } from '../grafico/configGrafico'
import type { SincronizadorTiempo } from '../grafico/sincronizadorTiempo'
import './CurvaCapital.css'

interface Props {
  estrategia: PuntoCurva[]
  buyAndHold: PuntoCurva[]
  moneda: string
  sincronizador: SincronizadorTiempo
}

function aLinea(curva: PuntoCurva[]): LineData[] {
  return curva.map((punto) => ({ time: punto.ts as UTCTimestamp, value: punto.capital }))
}

/** Curva de capital de la estrategia contra el Buy & Hold (mismo capital inicial). */
function CurvaCapital({ estrategia, buyAndHold, moneda, sincronizador }: Props) {
  const contenedor = useRef<HTMLDivElement>(null)
  const chartRef = useRef<IChartApi | null>(null)
  const serieEstrategia = useRef<ISeriesApi<'Line'> | null>(null)
  const serieBH = useRef<ISeriesApi<'Line'> | null>(null)

  useEffect(() => {
    if (!contenedor.current) return
    const chart = createChart(contenedor.current, {
      ...OPCIONES_GRAFICO,
      autoSize: true,
      timeScale: { ...OPCIONES_GRAFICO.timeScale, timeVisible: false },
    })
    chartRef.current = chart
    // El Buy & Hold va primero (debajo) y más tenue: es la referencia
    serieBH.current = chart.addLineSeries({
      color: '#6e7681',
      lineWidth: 1,
      lineStyle: 2, // punteada
      priceLineVisible: false,
      lastValueVisible: false,
    })
    serieEstrategia.current = chart.addLineSeries({
      color: COLORES.verde,
      lineWidth: 2,
      priceLineVisible: false,
    })
    const liberar = sincronizador.registrar(chart)
    return () => {
      liberar()
      chartRef.current = null
      serieEstrategia.current = null
      serieBH.current = null
      chart.remove()
    }
  }, [sincronizador])

  useEffect(() => {
    const chart = chartRef.current
    if (!serieEstrategia.current || !serieBH.current || !chart) return
    sincronizador.volcarYSincronizar(chart, () => {
      serieEstrategia.current?.setData(aLinea(estrategia))
      serieBH.current?.setData(aLinea(buyAndHold))
    })
  }, [estrategia, buyAndHold, sincronizador])

  return (
    <div className="curva-capital">
      <div className="leyenda-curva">
        <span className="serie-leyenda estrategia">━ Estrategia</span>
        <span className="serie-leyenda bh">╌ Buy &amp; Hold</span>
        <span className="nota-curva">capital en {moneda}</span>
      </div>
      <div ref={contenedor} className="area-curva" />
    </div>
  )
}

export default CurvaCapital
