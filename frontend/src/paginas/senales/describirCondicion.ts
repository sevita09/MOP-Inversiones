import type { CondicionDetalle } from '../../api/tipos'
import { ETIQUETA_TEMPORALIDAD, INDICADORES_REGLAS } from '../../componentes/bots/configReglas'

const OPERADOR_TEXTO: Record<string, string> = {
  mayor: 'está por encima de',
  menor: 'está por debajo de',
  cruza_arriba: 'cruzó hacia arriba',
  cruza_abajo: 'cruzó hacia abajo',
  cruza_arriba_precio: 'fue cruzada hacia arriba por el precio',
  cruza_abajo_precio: 'fue cruzada hacia abajo por el precio',
}

function nombreSerie(indicador: string, serie: string, params?: Record<string, number> | null): string {
  if (indicador === 'ema' && params?.periodo) return `EMA ${params.periodo}`
  const info = INDICADORES_REGLAS[indicador]
  return info?.series.find(({ valor }) => valor === serie)?.etiqueta ?? serie
}

function numero(valor: number | null): string {
  if (valor === null) return '—'
  return valor.toLocaleString('es-AR', { maximumFractionDigits: 2 }).replace('-', '−')
}

/** Frase de una condición con su valor real: "z-score (σ) mensual = −2,3 —
 *  está por debajo de −2". `sujeto` es el nombre + temporalidad + valor actual. */
export function describirCondicion(condicion: CondicionDetalle): {
  sujeto: string
  valor: string
  relacion: string
  cumple: boolean
} {
  const serie = nombreSerie(condicion.indicador, condicion.serie, condicion.params)
  const tf = ETIQUETA_TEMPORALIDAD[condicion.temporalidad].toLowerCase()
  const objetivo = condicion.objetivo_serie
    ? nombreSerie(condicion.indicador, condicion.objetivo_serie, condicion.params)
    : numero(condicion.objetivo)

  return {
    sujeto: `${serie} ${tf}`,
    valor: numero(condicion.valor),
    relacion: `${OPERADOR_TEXTO[condicion.operador] ?? condicion.operador} ${objetivo}`,
    cumple: condicion.cumple,
  }
}
