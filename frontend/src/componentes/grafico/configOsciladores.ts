// Definición declarativa de cada panel de oscilador: qué series dibuja, con qué
// estilo, y si tiene escala fija + líneas de referencia. Agregar un oscilador
// nuevo es sumar una entrada acá (y su indicador en el backend).

export type TipoSerieOsc = 'linea' | 'histograma'

export interface SerieOsc {
  clave: string // clave de la serie en la respuesta del indicador
  tipo: TipoSerieOsc
  color: string
  etiqueta: string // rótulo corto para la leyenda del crosshair
}

export interface ConfigOscilador {
  nombre: string // nombre del indicador en /api/indicadores
  titulo: string
  descripcion: string // explicación de una línea (tooltip)
  series: SerieOsc[]
  rango?: { min: number; max: number } // escala fija (RSI/estocástico: 0-100)
  referencias?: number[] // líneas horizontales de referencia
}

export const OSCILADORES: Record<string, ConfigOscilador> = {
  macd: {
    nombre: 'macd',
    titulo: 'MACD',
    descripcion: 'MACD: diferencia de medias (12/26) y su señal — momentum y giros de tendencia',
    series: [
      { clave: 'histograma', tipo: 'histograma', color: '#388bfd', etiqueta: 'Hist' },
      { clave: 'macd', tipo: 'linea', color: '#e3b341', etiqueta: 'MACD' },
      { clave: 'senal', tipo: 'linea', color: '#f85149', etiqueta: 'Señal' },
    ],
  },
  rsi: {
    nombre: 'rsi',
    titulo: 'RSI',
    descripcion: 'RSI: fuerza relativa 0–100; sobrecompra >70, sobreventa <30',
    series: [{ clave: 'rsi', tipo: 'linea', color: '#a371f7', etiqueta: 'RSI' }],
    rango: { min: 0, max: 100 },
    referencias: [30, 70],
  },
  estocastico: {
    nombre: 'estocastico',
    titulo: 'Estocástico',
    descripcion: 'Estocástico: posición del cierre en el rango reciente (0–100); >80 sobrecompra, <20 sobreventa',
    series: [
      { clave: 'k', tipo: 'linea', color: '#388bfd', etiqueta: '%K' },
      { clave: 'd', tipo: 'linea', color: '#e3b341', etiqueta: '%D' },
    ],
    rango: { min: 0, max: 100 },
    referencias: [20, 80],
  },
  atr: {
    nombre: 'atr',
    titulo: 'ATR',
    descripcion: 'ATR: rango verdadero promedio — volatilidad absoluta (útil para stops)',
    series: [{ clave: 'atr', tipo: 'linea', color: '#e3b341', etiqueta: 'ATR' }],
  },
  adx: {
    nombre: 'adx',
    titulo: 'ADX',
    descripcion: 'ADX: fuerza de la tendencia (0–100); >25 indica tendencia definida',
    series: [{ clave: 'adx', tipo: 'linea', color: '#a371f7', etiqueta: 'ADX' }],
    rango: { min: 0, max: 100 },
    referencias: [25],
  },
  porcentaje_b: {
    nombre: 'porcentaje_b',
    titulo: '%B Bollinger',
    descripcion: '%B: posición del precio dentro de las bandas de Bollinger (0 = banda inferior, 1 = superior)',
    series: [{ clave: 'porcentaje_b', tipo: 'linea', color: '#388bfd', etiqueta: '%B' }],
    rango: { min: -0.5, max: 1.5 },
    referencias: [0, 1],
  },
  percentil_distancia: {
    nombre: 'percentil_distancia',
    titulo: 'Percentil dist.',
    descripcion: 'Percentil de la distancia del precio a la EMA central respecto a su propia historia (0–100)',
    series: [{ clave: 'percentil', tipo: 'linea', color: '#3fb950', etiqueta: 'Pctil' }],
    rango: { min: 0, max: 100 },
    referencias: [20, 80],
  },
}

// Orden de aparición de los paneles bajo el precio
export const ORDEN_OSCILADORES = [
  'macd', 'rsi', 'estocastico', 'atr', 'adx', 'porcentaje_b', 'percentil_distancia',
] as const
export type NombreOscilador = (typeof ORDEN_OSCILADORES)[number]
