import type { TemporalidadBot } from '../../api/tipos'

/** Períodos de historia que comparten las vistas de análisis. */
export const PERIODOS: { clave: string; meses: number }[] = [
  { clave: '1M', meses: 1 },
  { clave: '3M', meses: 3 },
  { clave: '6M', meses: 6 },
  { clave: '1Y', meses: 12 },
  { clave: '2Y', meses: 24 },
  { clave: '5Y', meses: 60 },
  { clave: '10Y', meses: 120 },
]

/** Barras que entran en un mes de cada temporalidad. */
export const BARRAS_POR_MES: Record<TemporalidadBot, number> = { D: 21, S: 4.33, M: 1 }

/** La ventana móvil es un cuarto del período: así entran unas cuantas
 *  posiciones de la ventana dentro del tramo y la línea tiene recorrido. Con la
 *  ventana igual al período habría un solo punto. */
export const FRACCION_VENTANA = 4
export const VENTANA_MINIMA = 10

// Debajo de esto el coeficiente es más ruido que señal, y conviene avisarlo
export const MUESTRA_CONFIABLE = 30

export function desdeTs(meses: number): number {
  const fecha = new Date()
  fecha.setMonth(fecha.getMonth() - meses)
  return Math.floor(fecha.getTime() / 1000)
}
