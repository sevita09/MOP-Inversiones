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
