// Definición declarativa de cada panel de oscilador: qué series dibuja, con qué
// estilo, y si tiene escala fija + líneas de referencia. Agregar un oscilador
// nuevo es sumar una entrada acá (y su indicador en el backend).

export type TipoSerieOsc = 'linea' | 'histograma'

export interface SerieOsc {
  clave: string // clave de la serie en la respuesta del indicador
  tipo: TipoSerieOsc
  color: string
}

export interface ConfigOscilador {
  nombre: string // nombre del indicador en /api/indicadores
  titulo: string
  series: SerieOsc[]
  rango?: { min: number; max: number } // escala fija (RSI/estocástico: 0-100)
  referencias?: number[] // líneas horizontales de referencia
}

export const OSCILADORES: Record<string, ConfigOscilador> = {
  macd: {
    nombre: 'macd',
    titulo: 'MACD',
    series: [
      { clave: 'histograma', tipo: 'histograma', color: '#388bfd' },
      { clave: 'macd', tipo: 'linea', color: '#e3b341' },
      { clave: 'senal', tipo: 'linea', color: '#f85149' },
    ],
  },
  rsi: {
    nombre: 'rsi',
    titulo: 'RSI',
    series: [{ clave: 'rsi', tipo: 'linea', color: '#a371f7' }],
    rango: { min: 0, max: 100 },
    referencias: [30, 70],
  },
  estocastico: {
    nombre: 'estocastico',
    titulo: 'Estocástico',
    series: [
      { clave: 'k', tipo: 'linea', color: '#388bfd' },
      { clave: 'd', tipo: 'linea', color: '#e3b341' },
    ],
    rango: { min: 0, max: 100 },
    referencias: [20, 80],
  },
}

// Orden de aparición de los paneles bajo el precio
export const ORDEN_OSCILADORES = ['macd', 'rsi', 'estocastico'] as const
export type NombreOscilador = (typeof ORDEN_OSCILADORES)[number]
