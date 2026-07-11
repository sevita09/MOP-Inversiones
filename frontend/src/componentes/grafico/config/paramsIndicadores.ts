import type { Temporalidad } from '../../../api/tipos'
import type { ValorParam } from '../../../contextos/EstilosContext'

// Un parámetro configurable de un indicador. Numérico (período, desvíos) o, si
// trae `opciones`, una elección (p.ej. tipo de media: exponencial/simple).
export interface CampoParam {
  clave: string // clave que espera el backend (p.ej. 'periodo', 'tipo')
  etiqueta: string // rótulo en el diálogo
  recomendado: ValorParam // default del código (para el que NO depende de la temporalidad)
  paso?: number // salto del input numérico (1 para enteros, 0.1 para desvíos)
  min?: number
  opciones?: { valor: string; etiqueta: string }[] // si está, es un select
  // La ventana es la EMA central de la metodología → el recomendado depende de la
  // temporalidad (D=200, S=50, M=12); el diálogo lo resuelve con PERIODO_EMA_CENTRAL.
  emaCentral?: boolean
}

// Elección exponencial/simple, reutilizada por bandas y por las EMAs extra.
export const OPCIONES_TIPO_MEDIA = [
  { valor: 'exp', etiqueta: 'Exponencial' },
  { valor: 'simple', etiqueta: 'Simple' },
]

// EMA central por temporalidad (espejo de EMA_POR_TEMPORALIDAD del backend)
export const PERIODO_EMA_CENTRAL: Record<Temporalidad, number> = { H: 200, D: 200, S: 50, M: 12 }

export function recomendadoDe(campo: CampoParam, temporalidad: Temporalidad): ValorParam {
  return campo.emaCentral ? PERIODO_EMA_CENTRAL[temporalidad] : campo.recomendado
}

// Clave de guardado de un parámetro. Los campos de la EMA central se guardan por
// temporalidad (`periodo.D`, `periodo.S`, `periodo.M`): cada temporalidad tiene su
// propio valor y no se pisan entre sí. El resto usa la clave tal cual.
export function claveGuardada(campo: CampoParam, temporalidad: Temporalidad): string {
  return campo.emaCentral ? `${campo.clave}.${temporalidad}` : campo.clave
}

// Parámetros configurables por indicador (clave = nombre del indicador en el backend).
// El precio dibuja EMA y bandas desde el mismo indicador 'bandas': su período es la
// EMA central. Bollinger es aparte (SMA propia). Cada oscilador trae los suyos.
// Los campos de bandas se reparten entre las pestañas EMA central (período+tipo) y
// Bandas σ (los 3 multiplicadores), pero se envían todos juntos al backend.
export const CAMPOS_BANDAS: CampoParam[] = [
  { clave: 'periodo', etiqueta: 'Período', recomendado: 200, min: 1, emaCentral: true },
  { clave: 'tipo', etiqueta: 'Tipo de media', recomendado: 'exp', opciones: OPCIONES_TIPO_MEDIA },
  { clave: 'desvio1', etiqueta: 'σ banda 1', recomendado: 1, min: 0.1, paso: 0.1 },
  { clave: 'desvio2', etiqueta: 'σ banda 2', recomendado: 2, min: 0.1, paso: 0.1 },
  { clave: 'desvio3', etiqueta: 'σ banda 3', recomendado: 3, min: 0.1, paso: 0.1 },
]

export const PARAMS_POR_INDICADOR: Record<string, CampoParam[]> = {
  bandas: CAMPOS_BANDAS,
  bollinger: [
    { clave: 'periodo', etiqueta: 'Período', recomendado: 20, min: 1 },
    { clave: 'desvios', etiqueta: 'Desvíos σ', recomendado: 2, min: 0.1, paso: 0.1 },
  ],
  macd: [
    { clave: 'rapida', etiqueta: 'EMA rápida', recomendado: 12, min: 1 },
    { clave: 'lenta', etiqueta: 'EMA lenta', recomendado: 26, min: 1 },
    { clave: 'senal', etiqueta: 'Señal', recomendado: 9, min: 1 },
  ],
  rsi: [{ clave: 'periodo', etiqueta: 'Período', recomendado: 14, min: 1 }],
  estocastico: [
    { clave: 'periodo', etiqueta: 'Período', recomendado: 14, min: 1 },
    { clave: 'suavizado', etiqueta: 'Suavizado %D', recomendado: 3, min: 1 },
  ],
  atr: [{ clave: 'periodo', etiqueta: 'Período', recomendado: 14, min: 1 }],
  adx: [{ clave: 'periodo', etiqueta: 'Período', recomendado: 14, min: 1 }],
  porcentaje_b: [
    { clave: 'periodo', etiqueta: 'Período', recomendado: 20, min: 1 },
    { clave: 'desvios', etiqueta: 'Desvíos σ', recomendado: 2, min: 0.1, paso: 0.1 },
  ],
  percentil_distancia: [
    { clave: 'periodo', etiqueta: 'Período EMA', recomendado: 200, min: 1, emaCentral: true },
    { clave: 'ventana', etiqueta: 'Ventana', recomendado: 252, min: 1 },
  ],
}

// JSON de overrides efectivos de un indicador para el query de /api/indicadores.
// Resuelve las claves por temporalidad (`periodo.D` → `periodo`) según la temporalidad
// actual y descarta el resto. '' si el usuario no cambió nada para esta temporalidad.
export function paramsQueryDe(
  indicador: string,
  overrides: Record<string, ValorParam>,
  temporalidad: Temporalidad,
): string {
  const campos = PARAMS_POR_INDICADOR[indicador] ?? []
  const efectivos: Record<string, ValorParam> = {}
  for (const campo of campos) {
    const valor = overrides[claveGuardada(campo, temporalidad)]
    if (valor === undefined) continue
    // Descarta valores numéricos por debajo del mínimo (p.ej. período 0, que
    // rompería el indicador): se usa el default en su lugar.
    if (typeof valor === 'number' && campo.min != null && valor < campo.min) continue
    efectivos[campo.clave] = valor
  }
  return Object.keys(efectivos).length > 0 ? JSON.stringify({ [indicador]: efectivos }) : ''
}
