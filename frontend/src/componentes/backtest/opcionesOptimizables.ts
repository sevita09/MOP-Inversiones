import type { Bot, CondicionRegla, ParametroOptimizacion } from '../../api/tipos'
import { INDICADORES_REGLAS } from '../bots/configReglas'

export interface OpcionOptimizable {
  clave: string
  etiqueta: string
  actual: number
  // Rango sugerido alrededor del valor actual
  desde: number
  hasta: number
  paso: number
  base: Omit<ParametroOptimizacion, 'desde' | 'hasta' | 'paso'>
}

const BLOQUES: { clave: 'entrada' | 'salida' | 'filtros'; nombre: string }[] = [
  { clave: 'entrada', nombre: 'entrada' },
  { clave: 'salida', nombre: 'salida' },
  { clave: 'filtros', nombre: 'filtro' },
]

const CAMPOS_RIESGO: { campo: string; etiqueta: string; paso: number }[] = [
  { campo: 'stop_loss_pct', etiqueta: 'Stop loss (%)', paso: 2 },
  { campo: 'take_profit_pct', etiqueta: 'Take profit (%)', paso: 5 },
  { campo: 'trailing_pct', etiqueta: 'Trailing stop (%)', paso: 3 },
  { campo: 'stop_atr_mult', etiqueta: 'Stop por ATR (×)', paso: 0.5 },
  { campo: 'sizing_riesgo_pct', etiqueta: 'Riesgo por trade (%)', paso: 0.5 },
]

function nombreSerie(condicion: CondicionRegla): string {
  const info = INDICADORES_REGLAS[condicion.indicador]
  return info?.series.find(({ valor }) => valor === condicion.serie)?.etiqueta ?? condicion.serie
}

/** Rango sugerido: ±50% alrededor del valor actual, en ~6 pasos. */
function rangoSugerido(actual: number, pasoMinimo: number) {
  const amplitud = Math.abs(actual) * 0.5 || pasoMinimo * 3
  const paso = Math.max(pasoMinimo, Number((amplitud / 3).toPrecision(1)))
  return {
    desde: Number((actual - amplitud).toFixed(4)),
    hasta: Number((actual + amplitud).toFixed(4)),
    paso,
  }
}

/** Qué se puede barrer en este bot: umbrales de sus condiciones y su riesgo. */
export function opcionesOptimizables(bot: Bot): OpcionOptimizable[] {
  const opciones: OpcionOptimizable[] = []

  for (const { clave, nombre } of BLOQUES) {
    bot.reglas[clave].forEach((condicion, indice) => {
      // Umbral (objetivo numérico): el caso típico —"z < −2" barriendo el −2
      if (typeof condicion.objetivo === 'number') {
        opciones.push({
          clave: `${clave}.${indice}.objetivo`,
          etiqueta: `Umbral de ${nombreSerie(condicion)} (${nombre} ${indice + 1})`,
          actual: condicion.objetivo,
          ...rangoSugerido(condicion.objetivo, 0.1),
          base: { tipo: 'condicion', bloque: clave, indice, campo: 'objetivo' },
        })
      }
      // Período del indicador (p.ej. la EMA del gatillo diario)
      const periodo = condicion.params?.periodo
      if (typeof periodo === 'number') {
        opciones.push({
          clave: `${clave}.${indice}.periodo`,
          etiqueta: `Período de ${nombreSerie(condicion)} (${nombre} ${indice + 1})`,
          actual: periodo,
          ...rangoSugerido(periodo, 1),
          base: { tipo: 'condicion', bloque: clave, indice, campo: 'params.periodo' },
        })
      }
    })
  }

  for (const { campo, etiqueta, paso } of CAMPOS_RIESGO) {
    const actual = bot.riesgo[campo as keyof typeof bot.riesgo]
    if (typeof actual === 'number') {
      opciones.push({
        clave: `riesgo.${campo}`,
        etiqueta,
        actual,
        ...rangoSugerido(actual, paso),
        base: { tipo: 'riesgo', campo },
      })
    }
  }

  return opciones
}
