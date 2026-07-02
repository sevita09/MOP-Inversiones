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

// Gris para distinguirlo de la EMA (dorada) y las bandas σ (azules)
const COLOR_BOLLINGER = '#8b949e'
const CLAVES = ['inferior', 'media', 'superior'] as const

const BASE: LineSeriesPartialOptions = {
  color: COLOR_BOLLINGER,
  lineWidth: 1,
  priceLineVisible: false,
  lastValueVisible: false,
  crosshairMarkerVisible: false,
}

function datosSerie(ts: number[], valores: (number | null)[]): (LineData | WhitespaceData)[] {
  return ts.map((t, i) => {
    const valor = valores[i]
    return valor == null
      ? { time: t as UTCTimestamp }
      : { time: t as UTCTimestamp, value: valor }
  })
}

export function crearSeriesBollinger(chart: IChartApi): Map<string, ISeriesApi<'Line'>> {
  const series = new Map<string, ISeriesApi<'Line'>>()
  for (const clave of CLAVES) {
    // La media va punteada; las bandas, sólidas
    series.set(clave, chart.addLineSeries({
      ...BASE,
      lineStyle: clave === 'media' ? LineStyle.Dashed : LineStyle.Solid,
    }))
  }
  return series
}

export function volcarBollinger(
  series: Map<string, ISeriesApi<'Line'>>,
  datos: DatosBollinger | null,
): void {
  for (const [clave, serie] of series) {
    serie.setData(datos ? datosSerie(datos.ts, datos.series[clave] ?? []) : [])
  }
}
