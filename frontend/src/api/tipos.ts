export interface EstadoSalud {
  estado: string
  servicio: string
}

export type Temporalidad = 'H' | 'D' | 'S' | 'M'
export type Moneda = 'ARS' | 'USD'
export type TipoGrafico = 'velas' | 'linea' | 'area'
export type EscalaPrecio = 'lineal' | 'log'

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

export interface InfoAdr {
  simbolo: string
  ratio: number
}

export interface RespuestaVelas {
  ticker: string
  temporalidad: string
  moneda: Moneda
  velas: Vela[]
  adr: InfoAdr | null
}

export interface Paneles {
  panel_lider: string[]
  panel_general: string[]
  cedears: string[]
  indices: string[]
  cripto: string[]
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

// Cada serie de un indicador; null en las posiciones de warmup (sin valor)
export type SerieIndicador = (number | null)[]

export interface RespuestaIndicadores {
  ticker: string
  temporalidad: string
  moneda: Moneda
  ts: number[]
  indicadores: Record<string, Record<string, SerieIndicador>>
}

export interface EstadoActualizacion {
  actual: string
  ultima: string | null
  hay_nueva: boolean
  url_descarga: string
}

export interface Categoria {
  id: number
  nombre: string
  tickers: string[]
}

// --- Bots ---

export type TemporalidadBot = 'D' | 'S' | 'M'

export interface CapitalBot {
  inicial: number
  porcentaje_por_posicion: number
}

export type OperadorRegla =
  | 'mayor'
  | 'menor'
  | 'cruza_arriba'
  | 'cruza_abajo'
  | 'cruza_arriba_precio'
  | 'cruza_abajo_precio'

// Objetivo de una condición: constante, otra serie del mismo indicador, o nada
// (en los operadores *_precio, donde el cierre es quien cruza la serie)
export interface ObjetivoSerie {
  serie: string
  params?: Record<string, number>
}

export interface CondicionRegla {
  indicador: string
  serie: string
  operador: OperadorRegla
  objetivo?: number | ObjetivoSerie | null
  params?: Record<string, number>
}

export interface ReglasBot {
  version: number
  entrada: CondicionRegla[]
  salida: CondicionRegla[]
  filtros: CondicionRegla[]
}

export interface RespuestaPreview {
  ts_entrada: number[]
  ts_salida: number[]
}

export interface Bot {
  id: number
  nombre: string
  ticker: string
  temporalidad: TemporalidadBot
  moneda: Moneda
  capital: CapitalBot
  reglas: ReglasBot
  activo: boolean
  creado: string
  actualizado: string
}

export interface BotNuevo {
  nombre: string
  ticker: string
  temporalidad: TemporalidadBot
  moneda: Moneda
  capital: CapitalBot
  reglas?: ReglasBot
}
