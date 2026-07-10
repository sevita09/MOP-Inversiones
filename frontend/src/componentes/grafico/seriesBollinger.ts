import type {
  IChartApi,
  ISeriesApi,
  LineData,
  LineSeriesPartialOptions,
  UTCTimestamp,
  WhitespaceData,
} from 'lightweight-charts'
import { LineStyle } from 'lightweight-charts'
import type { DatosBollinger } from '../../hooks/usarBollinger'
import { aLineStyle, type Estilo } from '../../contextos/EstilosContext'

const CLAVES = ['inferior', 'media', 'superior'] as const

function opciones(clave: string, estilo: Estilo): LineSeriesPartialOptions {
  return {
    color: estilo.color,
    lineWidth: (estilo.ancho ?? 1) as LineSeriesPartialOptions['lineWidth'],
    // La media respeta el tipo elegido; las bandas van sólidas para distinguirse
    lineStyle: clave === 'media' ? aLineStyle(estilo.tipoLinea) : LineStyle.Solid,
    priceLineVisible: false,
    lastValueVisible: false,
    crosshairMarkerVisible: false,
  }
}

function datosSerie(ts: number[], valores: (number | null)[]): (LineData | WhitespaceData)[] {
  return ts.map((t, i) => {
    const valor = valores[i]
    return valor == null
      ? { time: t as UTCTimestamp }
      : { time: t as UTCTimestamp, value: valor }
  })
}

export function crearSeriesBollinger(
  chart: IChartApi,
  estilo: Estilo,
): Map<string, ISeriesApi<'Line'>> {
  const series = new Map<string, ISeriesApi<'Line'>>()
  for (const clave of CLAVES) {
    series.set(clave, chart.addLineSeries(opciones(clave, estilo)))
  }
  return series
}

export function aplicarEstiloBollinger(
  series: Map<string, ISeriesApi<'Line'>>,
  estilo: Estilo,
): void {
  for (const [clave, serie] of series) {
    serie.applyOptions(opciones(clave, estilo))
  }
}

export function volcarBollinger(
  series: Map<string, ISeriesApi<'Line'>>,
  datos: DatosBollinger | null,
): void {
  for (const [clave, serie] of series) {
    serie.setData(datos ? datosSerie(datos.ts, datos.series[clave] ?? []) : [])
  }
}
