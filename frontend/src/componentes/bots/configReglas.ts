import type { CondicionRegla, OperadorRegla, ReglasBot } from '../../api/tipos'

// Espejo de SERIES_POR_INDICADOR del backend (esquemas/reglas.py), con las
// etiquetas que ve el usuario. Si el registry suma un indicador, va acá también.
export interface InfoIndicador {
  etiqueta: string
  series: { valor: string; etiqueta: string }[]
}

export const INDICADORES_REGLAS: Record<string, InfoIndicador> = {
  bandas: {
    etiqueta: 'EMA central y bandas σ',
    series: [
      { valor: 'z', etiqueta: 'z-score (σ)' },
      { valor: 'media', etiqueta: 'EMA central' },
      { valor: 'sup1', etiqueta: 'banda +1σ' },
      { valor: 'sup2', etiqueta: 'banda +2σ' },
      { valor: 'sup3', etiqueta: 'banda +3σ' },
      { valor: 'inf1', etiqueta: 'banda −1σ' },
      { valor: 'inf2', etiqueta: 'banda −2σ' },
      { valor: 'inf3', etiqueta: 'banda −3σ' },
    ],
  },
  estocastico: {
    etiqueta: 'Estocástico',
    series: [
      { valor: 'k', etiqueta: '%K' },
      { valor: 'd', etiqueta: '%D' },
    ],
  },
  rsi: { etiqueta: 'RSI', series: [{ valor: 'rsi', etiqueta: 'RSI' }] },
  macd: {
    etiqueta: 'MACD',
    series: [
      { valor: 'macd', etiqueta: 'línea MACD' },
      { valor: 'senal', etiqueta: 'señal' },
      { valor: 'histograma', etiqueta: 'histograma' },
    ],
  },
  ema: { etiqueta: 'EMA', series: [{ valor: 'ema', etiqueta: 'EMA' }] },
  percentil_distancia: {
    etiqueta: 'Percentil de distancia',
    series: [{ valor: 'percentil', etiqueta: 'percentil' }],
  },
  bollinger: {
    etiqueta: 'Bollinger',
    series: [
      { valor: 'media', etiqueta: 'media' },
      { valor: 'superior', etiqueta: 'banda superior' },
      { valor: 'inferior', etiqueta: 'banda inferior' },
    ],
  },
  adx: { etiqueta: 'ADX', series: [{ valor: 'adx', etiqueta: 'ADX' }] },
  atr: { etiqueta: 'ATR', series: [{ valor: 'atr', etiqueta: 'ATR' }] },
  porcentaje_b: { etiqueta: '%B', series: [{ valor: 'porcentaje_b', etiqueta: '%B' }] },
}

export const OPERADORES_REGLAS: { valor: OperadorRegla; etiqueta: string }[] = [
  { valor: 'menor', etiqueta: 'es menor que' },
  { valor: 'mayor', etiqueta: 'es mayor que' },
  { valor: 'cruza_arriba', etiqueta: 'cruza hacia arriba' },
  { valor: 'cruza_abajo', etiqueta: 'cruza hacia abajo' },
  { valor: 'cruza_arriba_precio', etiqueta: 'el precio la cruza hacia arriba' },
  { valor: 'cruza_abajo_precio', etiqueta: 'el precio la cruza hacia abajo' },
]

export const ES_OPERADOR_PRECIO = (operador: OperadorRegla) => operador.endsWith('_precio')

export const CONDICION_NUEVA: CondicionRegla = {
  indicador: 'bandas',
  serie: 'z',
  operador: 'menor',
  objetivo: -2,
}

export const REGLAS_VACIAS: ReglasBot = { version: 1, entrada: [], salida: [], filtros: [] }

/** Al menos una condición en la entrada: lo mínimo para que un bot dispare. */
export function reglasConContenido(reglas: ReglasBot): boolean {
  return reglas.entrada.length > 0
}
