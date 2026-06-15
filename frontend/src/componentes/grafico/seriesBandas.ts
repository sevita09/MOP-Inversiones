import type {
  IChartApi,
  ISeriesApi,
  LineData,
  LineSeriesPartialOptions,
  UTCTimestamp,
  WhitespaceData,
} from 'lightweight-charts'
import type { DatosBandas } from '../../hooks/usarBandas'
import { COLOR_EMA_CENTRAL, COLORES_BANDAS } from './configGrafico'

// Las 6 bandas σ (sin la media). Orden de creación = orden de dibujo.
const CLAVES_BANDAS = ['inf3', 'inf2', 'inf1', 'sup1', 'sup2', 'sup3'] as const

// Opciones comunes: líneas auxiliares, sin etiqueta de precio ni marcador propio
const BASE: LineSeriesPartialOptions = {
  priceLineVisible: false,
  lastValueVisible: false,
  crosshairMarkerVisible: false,
}

function datosSerie(ts: number[], valores: (number | null)[]): (LineData | WhitespaceData)[] {
  // null (warmup) → punto en blanco: corta la línea sin inventar valores
  return ts.map((t, i) => {
    const valor = valores[i]
    return valor == null
      ? { time: t as UTCTimestamp }
      : { time: t as UTCTimestamp, value: valor }
  })
}

export function crearSerieEma(chart: IChartApi): ISeriesApi<'Line'> {
  return chart.addLineSeries({ ...BASE, color: COLOR_EMA_CENTRAL, lineWidth: 2 })
}

export function crearSeriesBandas(chart: IChartApi): Map<string, ISeriesApi<'Line'>> {
  const series = new Map<string, ISeriesApi<'Line'>>()
  for (const clave of CLAVES_BANDAS) {
    const sigma = Number(clave.slice(-1)) as 1 | 2 | 3
    series.set(clave, chart.addLineSeries({ ...BASE, color: COLORES_BANDAS[sigma], lineWidth: 1 }))
  }
  return series
}

export function volcarEma(serie: ISeriesApi<'Line'>, datos: DatosBandas | null): void {
  serie.setData(datos ? datosSerie(datos.ts, datos.series.media) : [])
}

export function volcarBandas(
  series: Map<string, ISeriesApi<'Line'>>,
  datos: DatosBandas | null,
): void {
  for (const [clave, serie] of series) {
    serie.setData(datos ? datosSerie(datos.ts, datos.series[clave] ?? []) : [])
  }
}
