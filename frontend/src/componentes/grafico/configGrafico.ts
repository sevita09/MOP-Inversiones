import { ColorType } from 'lightweight-charts'
import type {
  AreaSeriesPartialOptions,
  CandlestickSeriesPartialOptions,
  DeepPartial,
  ChartOptions,
  LineSeriesPartialOptions,
} from 'lightweight-charts'

// Paleta del tema oscuro (consistente con index.css)
export const COLORES = {
  fondo: '#0d1117',
  texto: '#8b949e',
  grilla: '#1c2128',
  borde: '#30363d',
  verde: '#3fb950',
  rojo: '#f85149',
  azul: '#388bfd',
} as const

export const OPCIONES_GRAFICO: DeepPartial<ChartOptions> = {
  layout: {
    background: { type: ColorType.Solid, color: COLORES.fondo },
    textColor: COLORES.texto,
    fontFamily: 'system-ui, -apple-system, sans-serif',
    attributionLogo: false,
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

export const OPCIONES_LINEA: LineSeriesPartialOptions = {
  color: COLORES.azul,
  lineWidth: 2,
}

export const OPCIONES_AREA: AreaSeriesPartialOptions = {
  lineColor: COLORES.azul,
  topColor: 'rgba(56, 139, 253, 0.4)',
  bottomColor: 'rgba(56, 139, 253, 0.02)',
  lineWidth: 2,
}

// Colores semitransparentes del histograma de volumen
export const VOLUMEN_VERDE = 'rgba(63, 185, 80, 0.45)'
export const VOLUMEN_ROJO = 'rgba(248, 81, 73, 0.45)'

// El volumen ocupa el 18% inferior del panel, sin escala visible propia
export const MARGENES_VOLUMEN = { top: 0.82, bottom: 0 }
