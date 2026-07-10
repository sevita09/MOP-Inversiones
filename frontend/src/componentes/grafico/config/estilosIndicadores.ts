import type { Estilo } from '../../../contextos/EstilosContext'
import { COLOR_EMA_CENTRAL } from '../configGrafico'
import { OSCILADORES } from '../configOsciladores'

export type CampoEstilo = 'color' | 'linea'

// Un elemento configurable (una línea/serie): su id de estilo, su rótulo, qué
// campos ofrece y su estilo recomendado (default del código).
export interface ElementoEstilo {
  id: string
  etiqueta: string
  campos: CampoEstilo[]
  recomendado: Estilo
}

// Grupo: un indicador puede tener una o varias líneas
export interface GrupoConfig {
  titulo: string
  elementos: ElementoEstilo[]
}

// Lo que abre el diálogo: un título y uno o varios grupos (mostrados como pestañas)
export interface AperturaConfig {
  titulo: string
  grupos: GrupoConfig[]
}

// Estilos recomendados de los indicadores del panel de precio
export const REC_EMA: Estilo = { color: COLOR_EMA_CENTRAL, ancho: 2, tipoLinea: 'solid' }
export const REC_BANDAS: Estilo = { color: '#388bfd', ancho: 1, tipoLinea: 'solid' }
export const REC_BOLLINGER: Estilo = { color: '#8b949e', ancho: 1, tipoLinea: 'dashed' }

// Opacidad de cada banda σ sobre el color base (±1σ la más marcada, ±3σ la más sutil)
export const OPACIDAD_SIGMA: Record<1 | 2 | 3, number> = { 1: 0.55, 2: 0.38, 3: 0.22 }

export const GRUPO_EMA: GrupoConfig = {
  titulo: 'EMA central',
  elementos: [{ id: 'ema', etiqueta: 'Línea', campos: ['color', 'linea'], recomendado: REC_EMA }],
}
export const GRUPO_BANDAS: GrupoConfig = {
  titulo: 'Bandas σ',
  elementos: [{ id: 'bandas', etiqueta: 'Bandas', campos: ['color', 'linea'], recomendado: REC_BANDAS }],
}
export const GRUPO_BOLLINGER: GrupoConfig = {
  titulo: 'Bollinger',
  elementos: [{ id: 'bollinger', etiqueta: 'Líneas', campos: ['color', 'linea'], recomendado: REC_BOLLINGER }],
}

// Grupo de configuración de un oscilador: una sección por cada serie que dibuja
export function grupoOscilador(nombre: string): GrupoConfig {
  const config = OSCILADORES[nombre]
  return {
    titulo: config.titulo,
    elementos: config.series.map((def) => ({
      id: `osc.${nombre}.${def.clave}`,
      etiqueta: def.etiqueta,
      campos: def.tipo === 'histograma' ? ['color'] : ['color', 'linea'],
      recomendado: { color: def.color, ancho: 1, tipoLinea: 'solid' },
    })),
  }
}

// La tuerca única de la barra abre EMA / σ / BB en pestañas
export const APERTURA_PRECIO: AperturaConfig = {
  titulo: 'Indicadores del precio',
  grupos: [GRUPO_EMA, GRUPO_BANDAS, GRUPO_BOLLINGER],
}

// La tuerca de un oscilador abre solo ese indicador (una sola pestaña)
export function aperturaOscilador(nombre: string): AperturaConfig {
  const grupo = grupoOscilador(nombre)
  return { titulo: grupo.titulo, grupos: [grupo] }
}
