export interface EstadoSalud {
  estado: string
  servicio: string
}

export type Temporalidad = 'H' | 'D' | 'S' | 'M'
export type Moneda = 'ARS' | 'USD'

export interface Vela {
  ticker: string
  temporalidad: string
  ts: number
  apertura: number
  maximo: number
  minimo: number
  cierre: number
  volumen: number
  es_faltante: number
}

export interface RespuestaVelas {
  ticker: string
  temporalidad: string
  moneda: Moneda
  velas: Vela[]
}

export interface Paneles {
  panel_lider: string[]
  panel_general: string[]
  cedears: string[]
  dolar: string[]
}

export interface Precio {
  cierre: number
  variacion_pct: number | null
}

export type Precios = Record<string, Precio>

export interface Tasa {
  fecha: string
  tipo: string
  valor: number
}

export interface RespuestaDolar {
  ccl: Tasa | null
  oficial: Tasa | null
}
