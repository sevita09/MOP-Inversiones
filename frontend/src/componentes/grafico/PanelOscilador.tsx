import { useEffect, useRef } from 'react'
import { createChart, LineStyle } from 'lightweight-charts'
import type {
  IChartApi,
  ISeriesApi,
  LineData,
  SeriesType,
  UTCTimestamp,
  WhitespaceData,
} from 'lightweight-charts'
import type { Moneda, SerieIndicador, Temporalidad } from '../../api/tipos'
import { usarIndicador } from '../../hooks/usarIndicador'
import { COLORES, OPCIONES_GRAFICO } from './configGrafico'
import type { ConfigOscilador } from './configOsciladores'
import type { SincronizadorTiempo } from './sincronizadorTiempo'
import './PanelOscilador.css'

function puntosLinea(ts: number[], valores: SerieIndicador): (LineData | WhitespaceData)[] {
  return ts.map((t, i) => {
    const valor = valores[i]
    return valor == null
      ? { time: t as UTCTimestamp }
      : { time: t as UTCTimestamp, value: valor }
  })
}

// El histograma del MACD se colorea por signo (verde sobre cero, rojo bajo cero)
function puntosHistograma(ts: number[], valores: SerieIndicador) {
  return ts.map((t, i) => {
    const valor = valores[i]
    if (valor == null) return { time: t as UTCTimestamp }
    return {
      time: t as UTCTimestamp,
      value: valor,
      color: valor >= 0 ? COLORES.verde : COLORES.rojo,
    }
  })
}

interface Props {
  config: ConfigOscilador
  ticker: string
  temporalidad: Temporalidad
  moneda: Moneda
  sincronizador: SincronizadorTiempo
}

function PanelOscilador({ config, ticker, temporalidad, moneda, sincronizador }: Props) {
  const contenedor = useRef<HTMLDivElement>(null)
  const series = useRef<Map<string, ISeriesApi<SeriesType>>>(new Map())
  const datos = usarIndicador(ticker, temporalidad, moneda, config.nombre, true)
  const datosRef = useRef(datos)
  datosRef.current = datos

  // Crear el chart, sus series y sincronizarlo (una sola vez)
  useEffect(() => {
    if (!contenedor.current) return
    const chart = createChart(contenedor.current, {
      ...OPCIONES_GRAFICO,
      autoSize: true,
      timeScale: { ...OPCIONES_GRAFICO.timeScale, visible: false },
    })

    // Escala fija (RSI/estocástico 0-100) vía autoscaleInfoProvider
    const proveedor = config.rango
      ? () => ({ priceRange: { minValue: config.rango!.min, maxValue: config.rango!.max } })
      : undefined

    config.series.forEach((def, indice) => {
      const serie =
        def.tipo === 'histograma'
          ? chart.addHistogramSeries({ color: def.color, priceLineVisible: false })
          : chart.addLineSeries({
              color: def.color,
              lineWidth: 1,
              priceLineVisible: false,
              lastValueVisible: false,
              autoscaleInfoProvider: proveedor,
            })
      // Las líneas de referencia (20/80) cuelgan de la primera serie
      if (indice === 0) {
        for (const nivel of config.referencias ?? []) {
          serie.createPriceLine({
            price: nivel,
            color: COLORES.borde,
            lineStyle: LineStyle.Dashed,
            lineWidth: 1,
            axisLabelVisible: true,
            title: '',
          })
        }
      }
      series.current.set(def.clave, serie)
    })

    volcar(series.current, datosRef.current, config)
    const liberar = sincronizador.registrar(chart)

    return () => {
      liberar()
      chart.remove()
      series.current.clear()
    }
    // Solo al montar: el chart y sus series no cambian con los props de datos
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  // Volcar los datos cuando cambian (ticker/temporalidad/moneda)
  useEffect(() => {
    volcar(series.current, datos, config)
  }, [datos, config])

  return (
    <div className="panel-oscilador">
      <span className="oscilador-titulo">{config.titulo}</span>
      <div ref={contenedor} className="oscilador-grafico" />
    </div>
  )
}

function volcar(
  series: Map<string, ISeriesApi<SeriesType>>,
  datos: { ts: number[]; series: Record<string, SerieIndicador> } | null,
  config: ConfigOscilador,
) {
  for (const def of config.series) {
    const serie = series.get(def.clave)
    if (!serie) continue
    if (!datos) {
      serie.setData([])
      continue
    }
    const valores = datos.series[def.clave] ?? []
    serie.setData(
      def.tipo === 'histograma'
        ? puntosHistograma(datos.ts, valores)
        : puntosLinea(datos.ts, valores),
    )
  }
}

export default PanelOscilador
