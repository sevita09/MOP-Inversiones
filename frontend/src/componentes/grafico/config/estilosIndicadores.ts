import type { Estilo } from '../../../contextos/EstilosContext'
import { COLOR_EMA_CENTRAL } from '../configGrafico'
import { OSCILADORES } from '../configOsciladores'
import { CAMPOS_BANDAS, PARAMS_POR_INDICADOR, type CampoParam } from './paramsIndicadores'

export type CampoEstilo = 'color' | 'linea' | 'opacidad'

// Un elemento configurable (una línea/serie): su id de estilo, su rótulo, qué
// campos ofrece y su estilo recomendado (default del código).
export interface ElementoEstilo {
  id: string
  etiqueta: string
  campos: CampoEstilo[]
  recomendado: Estilo
}

// Grupo: un indicador puede tener una o varias líneas. `indicador` es el nombre
// backend (para los parámetros numéricos); `params` sus campos configurables.
export interface GrupoConfig {
  titulo: string
  elementos: ElementoEstilo[]
  indicador?: string
  params?: CampoParam[]
  emasExtra?: boolean // muestra la sección para agregar EMAs extra (solo EMA central)
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

// VPVR: histogramas alcista/bajista (color + opacidad) y línea del POC
export const REC_VPVR_SUBE: Estilo = { color: '#3fb950', opacidad: 0.45 }
export const REC_VPVR_BAJA: Estilo = { color: '#f85149', opacidad: 0.45 }
export const REC_VPVR_POC: Estilo = { color: '#f85149', ancho: 2, tipoLinea: 'solid', opacidad: 1 }

// Opacidad de cada banda σ sobre el color base (±1σ la más marcada, ±3σ la más sutil)
export const OPACIDAD_SIGMA: Record<1 | 2 | 3, number> = { 1: 0.55, 2: 0.38, 3: 0.22 }

// La EMA central y las bandas salen del mismo indicador backend 'bandas'. Sus
// parámetros se reparten: período + tipo (exp/simple) en la pestaña EMA central,
// los 3 multiplicadores σ en la de Bandas. Se envían todos juntos igual.
export const GRUPO_EMA: GrupoConfig = {
  titulo: 'EMA central',
  indicador: 'bandas',
  params: CAMPOS_BANDAS.filter((c) => c.clave === 'periodo' || c.clave === 'tipo'),
  emasExtra: true,
  elementos: [{ id: 'ema', etiqueta: 'Línea', campos: ['color', 'linea'], recomendado: REC_EMA }],
}
export const GRUPO_BANDAS: GrupoConfig = {
  titulo: 'Bandas σ',
  indicador: 'bandas',
  params: CAMPOS_BANDAS.filter((c) => c.clave.startsWith('desvio')),
  elementos: [{ id: 'bandas', etiqueta: 'Bandas', campos: ['color', 'linea'], recomendado: REC_BANDAS }],
}
export const GRUPO_BOLLINGER: GrupoConfig = {
  titulo: 'Bollinger',
  indicador: 'bollinger',
  params: PARAMS_POR_INDICADOR.bollinger,
  elementos: [{ id: 'bollinger', etiqueta: 'Líneas', campos: ['color', 'linea'], recomendado: REC_BOLLINGER }],
}

// Grupo de configuración de un oscilador: una sección por cada serie que dibuja
export function grupoOscilador(nombre: string): GrupoConfig {
  const config = OSCILADORES[nombre]
  return {
    titulo: config.titulo,
    indicador: nombre,
    params: PARAMS_POR_INDICADOR[nombre],
    elementos: config.series.map((def) => ({
      id: `osc.${nombre}.${def.clave}`,
      etiqueta: def.etiqueta,
      campos: def.tipo === 'histograma' ? ['color'] : ['color', 'linea'],
      recomendado: { color: def.color, ancho: 1, tipoLinea: 'solid' },
    })),
  }
}

export const GRUPO_VPVR: GrupoConfig = {
  titulo: 'Vol L',
  elementos: [
    { id: 'vpvr.sube', etiqueta: 'Vol. alcista', campos: ['color', 'opacidad'], recomendado: REC_VPVR_SUBE },
    { id: 'vpvr.baja', etiqueta: 'Vol. bajista', campos: ['color', 'opacidad'], recomendado: REC_VPVR_BAJA },
    { id: 'vpvr.poc', etiqueta: 'Línea POC', campos: ['color', 'linea', 'opacidad'], recomendado: REC_VPVR_POC },
  ],
}

// Marcas de la cartera sobre el gráfico: compras abiertas y precio promedio
export const REC_PPC_COMPRA: Estilo = {
  color: '#a371f7', ancho: 1, tipoLinea: 'dashed', opacidad: 0.55,
}
export const REC_PPC_LINEA: Estilo = {
  color: '#a371f7', ancho: 2, tipoLinea: 'solid', opacidad: 1,
}

export const GRUPO_PPC: GrupoConfig = {
  titulo: 'PPC',
  elementos: [
    {
      id: 'ppc.compra',
      etiqueta: 'Compras abiertas',
      campos: ['color', 'linea', 'opacidad'],
      recomendado: REC_PPC_COMPRA,
    },
    {
      id: 'ppc.promedio',
      etiqueta: 'Precio promedio',
      campos: ['color', 'linea', 'opacidad'],
      recomendado: REC_PPC_LINEA,
    },
  ],
}

// La tuerca única de la barra abre EMA / σ / BB / Vol L / PPC en pestañas
export const APERTURA_PRECIO: AperturaConfig = {
  titulo: 'Indicadores del precio',
  grupos: [GRUPO_EMA, GRUPO_BANDAS, GRUPO_BOLLINGER, GRUPO_VPVR, GRUPO_PPC],
}

// La tuerca de un oscilador abre solo ese indicador (una sola pestaña)
export function aperturaOscilador(nombre: string): AperturaConfig {
  const grupo = grupoOscilador(nombre)
  return { titulo: grupo.titulo, grupos: [grupo] }
}
