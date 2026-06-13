import { ColorType } from 'lightweight-charts'
import type {
  CandlestickSeriesPartialOptions,
  DeepPartial,
  ChartOptions,
} from 'lightweight-charts'

// Paleta del tema oscuro (consistente con index.css)
export const COLORES = {
  fondo: '#0d1117',
  texto: '#8b949e',
  grilla: '#1c2128',
  borde: '#30363d',
  verde: '#3fb950',
  rojo: '#f85149',
} as const

export const OPCIONES_GRAFICO: DeepPartial<ChartOptions> = {
  layout: {
    background: { type: ColorType.Solid, color: COLORES.fondo },
    textColor: COLORES.texto,
    fontFamily: 'system-ui, -apple-system, sans-serif',
  },
  grid: {
    vertLines: { color: COLORES.grilla },
    horzLines: { color: COLORES.grilla },
  },
  rightPriceScale: { borderColor: COLORES.borde },
  timeScale: { borderColor: COLORES.borde, timeVisible: true },
  crosshair: { mode: 0 },
}

export const OPCIONES_VELAS: CandlestickSeriesPartialOptions = {
  upColor: COLORES.verde,
  downColor: COLORES.rojo,
  borderUpColor: COLORES.verde,
  borderDownColor: COLORES.rojo,
  wickUpColor: COLORES.verde,
  wickDownColor: COLORES.rojo,
}
