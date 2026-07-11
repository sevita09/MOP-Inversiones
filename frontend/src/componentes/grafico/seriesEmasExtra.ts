import type {
  IChartApi,
  ISeriesApi,
  LineData,
  LineSeriesPartialOptions,
  UTCTimestamp,
  WhitespaceData,
} from 'lightweight-charts'
import type { Vela } from '../../api/tipos'
import { aLineStyle, type TipoLinea } from '../../contextos/EstilosContext'

const BASE: LineSeriesPartialOptions = {
  priceLineVisible: false,
  lastValueVisible: false,
  crosshairMarkerVisible: false,
}

// Una EMA extra ya resuelta para la temporalidad actual: sus valores calculados y
// su estilo. El rótulo y el color se usan también en la leyenda del crosshair.
export interface EmaCalculada {
  id: string
  etiqueta: string
  color: string
  ancho: number
  tipoLinea: TipoLinea
  valores: (number | null)[]
}

function datosSerie(velas: Vela[], valores: (number | null)[]): (LineData | WhitespaceData)[] {
  return velas.map((vela, i) => {
    const valor = valores[i]
    return valor == null
      ? { time: vela.ts as UTCTimestamp }
      : { time: vela.ts as UTCTimestamp, value: valor }
  })
}

// Sincroniza el Map de series con la lista de EMAs extra: crea las nuevas, quita
// las que ya no están, y vuelca datos + estilo. Con el toggle apagado se llama con
// emas=[] para limpiar todo.
export function sincronizarEmasExtra(
  chart: IChartApi,
  mapa: Map<string, ISeriesApi<'Line'>>,
  emas: EmaCalculada[],
  velas: Vela[],
): void {
  const vigentes = new Set(emas.map((e) => e.id))
  for (const [id, serie] of mapa) {
    if (!vigentes.has(id)) {
      try {
        chart.removeSeries(serie)
      } catch {
        /* chart disposed */
      }
      mapa.delete(id)
    }
  }

  for (const ema of emas) {
    let serie = mapa.get(ema.id)
    if (!serie) {
      serie = chart.addLineSeries(BASE)
      mapa.set(ema.id, serie)
    }
    serie.applyOptions({
      color: ema.color,
      lineWidth: ema.ancho as LineSeriesPartialOptions['lineWidth'],
      lineStyle: aLineStyle(ema.tipoLinea),
    })
    serie.setData(datosSerie(velas, ema.valores))
  }
}

export function limpiarEmasExtra(
  chart: IChartApi,
  mapa: Map<string, ISeriesApi<'Line'>>,
): void {
  for (const serie of mapa.values()) {
    try {
      chart.removeSeries(serie)
    } catch {
      /* chart disposed */
    }
  }
  mapa.clear()
}
