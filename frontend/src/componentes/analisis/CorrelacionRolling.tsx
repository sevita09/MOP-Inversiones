import { useEffect, useRef } from 'react'
import { createChart } from 'lightweight-charts'
import type { IChartApi, ISeriesApi, UTCTimestamp } from 'lightweight-charts'
import type { PuntoRolling } from '../../api/tipos'
import { COLORES, OPCIONES_GRAFICO } from '../grafico/configGrafico'
import './CorrelacionRolling.css'

interface Props {
  puntos: PuntoRolling[]
  ventana: number
  total: number | null
}

/** Correlación móvil de un par a lo largo del tiempo.
 *
 *  Un coeficiente único sobre años esconde lo que importa: dos papeles pueden
 *  estar descorrelacionados mucho tiempo y pegarse en una crisis, que es justo
 *  cuando la diversificación tendría que servir. */
function CorrelacionRolling({ puntos, ventana, total }: Props) {
  const contenedor = useRef<HTMLDivElement>(null)
  const chartRef = useRef<IChartApi | null>(null)
  const serie = useRef<ISeriesApi<'Line'> | null>(null)
  const referencia = useRef<ISeriesApi<'Line'> | null>(null)

  useEffect(() => {
    if (!contenedor.current) return
    const chart = createChart(contenedor.current, {
      ...OPCIONES_GRAFICO,
      autoSize: true,
      timeScale: { ...OPCIONES_GRAFICO.timeScale, timeVisible: false },
    })
    chartRef.current = chart
    // La media del período, punteada: la línea móvil se lee contra ella
    referencia.current = chart.addLineSeries({
      color: '#6e7681',
      lineWidth: 1,
      lineStyle: 2,
      priceLineVisible: false,
      lastValueVisible: false,
    })
    serie.current = chart.addLineSeries({
      color: COLORES.azul,
      lineWidth: 2,
      priceLineVisible: false,
    })
    return () => {
      chartRef.current = null
      serie.current = null
      referencia.current = null
      chart.remove()
    }
  }, [])

  useEffect(() => {
    if (!serie.current || !referencia.current) return
    const datos = puntos.map((punto) => ({
      time: punto.ts as UTCTimestamp,
      value: punto.correlacion,
    }))
    serie.current.setData(datos)
    referencia.current.setData(
      total === null ? [] : datos.map((punto) => ({ time: punto.time, value: total })),
    )
    chartRef.current?.timeScale().fitContent()
  }, [puntos, total])

  return (
    <div className="correlacion-rolling">
      <div className="leyenda-rolling">
        <span className="serie-rolling movil">━ Ventana de {ventana} ruedas</span>
        {total !== null && (
          <span className="serie-rolling total">╌ Todo el período: {total.toFixed(2)}</span>
        )}
      </div>
      <div ref={contenedor} className="area-rolling" />
    </div>
  )
}

export default CorrelacionRolling
