import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { createChart, LineStyle } from 'lightweight-charts'
import type {
  IChartApi,
  ISeriesApi,
  LineData,
  MouseEventParams,
  SeriesType,
  UTCTimestamp,
  WhitespaceData,
} from 'lightweight-charts'
import type { Moneda, SerieIndicador, Temporalidad } from '../../api/tipos'
import { usarIndicador } from '../../hooks/usarIndicador'
import { usarEstilos, aLineStyle, type Estilo } from '../../contextos/EstilosContext'
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
  tsActivo?: number | null
  alMoverCrosshair?: (ts: number | null) => void
}

function formatearValor(valor: number | null): string {
  if (valor == null) return '—'
  return valor.toLocaleString('es-AR', { maximumFractionDigits: 2 })
}

const ALTURA_MIN = 60
const ALTURA_MAX = 350
const ALTURA_INICIAL = 130

function PanelOscilador({
  config,
  ticker,
  temporalidad,
  moneda,
  sincronizador,
  tsActivo = null,
  alMoverCrosshair,
}: Props) {
  const contenedor = useRef<HTMLDivElement>(null)
  const grafico = useRef<IChartApi | null>(null)
  const series = useRef<Map<string, ISeriesApi<SeriesType>>>(new Map())
  const datos = usarIndicador(ticker, temporalidad, moneda, config.nombre, true)
  const datosRef = useRef(datos)
  datosRef.current = datos
  const alMoverRef = useRef(alMoverCrosshair)
  alMoverRef.current = alMoverCrosshair
  const [altura, setAltura] = useState(ALTURA_INICIAL)

  // Estilo efectivo (recomendado + override del usuario) de cada serie del oscilador
  const { estiloDe } = usarEstilos()
  const estilos: Record<string, Estilo> = {}
  for (const def of config.series) {
    estilos[def.clave] = estiloDe(`osc.${config.nombre}.${def.clave}`, {
      color: def.color,
      ancho: 1,
      tipoLinea: 'solid',
    })
  }
  const estilosRef = useRef(estilos)
  estilosRef.current = estilos
  const firmaEstilos = config.series
    .map((d) => `${estilos[d.clave].color}|${estilos[d.clave].ancho}|${estilos[d.clave].tipoLinea}`)
    .join(',')

  // Valor de cada serie bajo el crosshair (ts compartido); sin crosshair, el último
  const indicePorTs = useMemo(() => {
    const mapa = new Map<number, number>()
    datos?.ts.forEach((t, i) => mapa.set(t, i))
    return mapa
  }, [datos])
  const indice =
    (tsActivo != null ? indicePorTs.get(tsActivo) : undefined) ??
    (datos ? datos.ts.length - 1 : -1)

  const alArrastrar = useCallback((e: React.MouseEvent) => {
    e.preventDefault()
    const yInicial = e.clientY
    const alturaInicial = altura
    const mover = (ev: MouseEvent) => {
      const delta = yInicial - ev.clientY
      setAltura(Math.min(ALTURA_MAX, Math.max(ALTURA_MIN, alturaInicial + delta)))
    }
    const soltar = () => {
      document.removeEventListener('mousemove', mover)
      document.removeEventListener('mouseup', soltar)
    }
    document.addEventListener('mousemove', mover)
    document.addEventListener('mouseup', soltar)
  }, [altura])

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
      const est = estilosRef.current[def.clave]
      const serie =
        def.tipo === 'histograma'
          ? chart.addHistogramSeries({ color: est.color, priceLineVisible: false })
          : chart.addLineSeries({
              color: est.color,
              lineWidth: (est.ancho ?? 1) as 1 | 2 | 3 | 4,
              lineStyle: aLineStyle(est.tipoLinea),
              priceLineVisible: false,
              lastValueVisible: false,
              autoscaleInfoProvider: proveedor,
            })
      // Las líneas de referencia (20/80) cuelgan de la primera serie
      if (indice === 0) {
        for (const nivel of config.referencias ?? []) {
          serie.createPriceLine({
            price: nivel,
            color: 'rgba(255, 255, 255, 0.3)',
            lineStyle: LineStyle.Dashed,
            lineWidth: 1,
            axisLabelVisible: true,
            title: '',
          })
        }
      }
      series.current.set(def.clave, serie)
    })

    grafico.current = chart
    sincronizador.volcarYSincronizar(chart, () => volcar(series.current, datosRef.current, config))
    const liberar = sincronizador.registrar(chart)

    const alMover = (parametros: MouseEventParams) => {
      const ts = parametros.time as number | undefined
      alMoverRef.current?.(ts ?? null)
    }
    chart.subscribeCrosshairMove(alMover)

    return () => {
      liberar()
      chart.unsubscribeCrosshairMove(alMover)
      chart.remove()
      grafico.current = null
      series.current.clear()
    }
    // Solo al montar: el chart y sus series no cambian con los props de datos
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  // Volcar los datos cuando cambian (ticker/temporalidad/moneda)
  useEffect(() => {
    const chart = grafico.current
    if (chart) {
      sincronizador.volcarYSincronizar(chart, () => volcar(series.current, datos, config))
    } else {
      volcar(series.current, datos, config)
    }
  }, [datos, config, sincronizador])

  // Aplicar el estilo del usuario en vivo (doble click en la leyenda del oscilador)
  useEffect(() => {
    for (const def of config.series) {
      const serie = series.current.get(def.clave)
      if (!serie) continue
      const est = estilosRef.current[def.clave]
      serie.applyOptions(
        def.tipo === 'histograma'
          ? { color: est.color }
          : { color: est.color, lineWidth: (est.ancho ?? 1) as 1 | 2 | 3 | 4, lineStyle: aLineStyle(est.tipoLinea) },
      )
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [firmaEstilos])

  return (
    <div className="panel-oscilador" style={{ height: altura }}>
      <div className="oscilador-handle" onMouseDown={alArrastrar} />
      <span className="oscilador-leyenda">
        <span className="oscilador-titulo">{config.titulo}</span>
        {config.series.map((def) => (
          <span
            key={def.clave}
            className="oscilador-valor"
            style={{ color: estilos[def.clave].color }}
          >
            {def.etiqueta} <b>{formatearValor(datos?.series[def.clave]?.[indice] ?? null)}</b>
          </span>
        ))}
      </span>
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
