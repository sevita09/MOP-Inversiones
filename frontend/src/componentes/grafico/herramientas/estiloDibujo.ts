import type { Estilo, TipoLinea } from '../../../contextos/EstilosContext'

// El estilo de un dibujo reutiliza la forma de los indicadores: color/ancho/tipoLinea.
export type EstiloDibujo = Estilo

// Recomendado (constante del código) de las herramientas de dibujo.
export const RECOMENDADO_DIBUJO: Estilo = { color: '#e3b341', ancho: 1, tipoLinea: 'solid' }

// Qué campos ofrece el diálogo por herramienta. La medición NO expone color: su
// verde/rojo es semántico (ganancia/pérdida); solo se le configura ancho y línea.
export function camposDibujo(tipo: string): ('color' | 'linea')[] {
  return tipo === 'medicion' ? ['linea'] : ['color', 'linea']
}

// Patrón de guiones para canvas según el tipo de línea (sólida = sin dash).
export function dashDe(tipoLinea: TipoLinea | undefined): number[] {
  if (tipoLinea === 'dashed') return [6, 4]
  if (tipoLinea === 'dotted') return [1, 3]
  return []
}

// Clave en el store de estilos (mop.estilos) para el default de una herramienta.
export function idHerramienta(tipo: string): string {
  return `herr.${tipo}`
}

// Estilo efectivo de un dibujo: lo guardado en su `datos.estilo`; para dibujos
// viejos sin él, cae al `datos.color` (horizontales) y al recomendado.
export function estiloDeDibujo(datos: Record<string, unknown>): EstiloDibujo {
  const guardado = (datos.estilo as EstiloDibujo) ?? {}
  const colorViejo = datos.color as string | undefined
  return {
    ...RECOMENDADO_DIBUJO,
    ...(colorViejo ? { color: colorViejo } : {}),
    ...guardado,
  }
}
