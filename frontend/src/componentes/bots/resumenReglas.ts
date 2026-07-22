import type { CondicionRegla, ReglasBot, TemporalidadBot } from '../../api/tipos'
import { ETIQUETA_TEMPORALIDAD, INDICADORES_REGLAS } from './configReglas'

/** "Compra cuando el z-score mensual está bajo −2 y el %K diario cruza hacia
 *  arriba el %D; vende cuando el z-score semanal está sobre 0." */
export function resumirReglas(reglas: ReglasBot, temporalidadBot: TemporalidadBot): string {
  const entrada = reglas.entrada.map((c) => frase(c, temporalidadBot))
  const filtros = reglas.filtros.map((c) => frase(c, temporalidadBot))
  const salida = reglas.salida.map((c) => frase(c, temporalidadBot))

  if (entrada.length === 0) return ''
  let texto = `Compra cuando ${unir(entrada)}`
  if (filtros.length > 0) texto += `, siempre que ${unir(filtros)}`
  if (salida.length > 0) texto += `; vende cuando ${unir(salida)}`
  return texto + '.'
}

function unir(frases: string[]): string {
  if (frases.length <= 1) return frases.join('')
  return `${frases.slice(0, -1).join(', ')} y ${frases[frases.length - 1]}`
}

function frase(condicion: CondicionRegla, temporalidadBot: TemporalidadBot): string {
  const serie = nombreSerie(condicion.indicador, condicion.serie, condicion.params)
  const tf = ETIQUETA_TEMPORALIDAD[condicion.temporalidad ?? temporalidadBot].toLowerCase()
  const sujeto = `${articulo(serie)} ${serie} ${tf}`

  switch (condicion.operador) {
    case 'mayor':
      return `${sujeto} está sobre ${numero(condicion)}`
    case 'menor':
      return `${sujeto} está bajo ${numero(condicion)}`
    case 'cruza_arriba':
      return `${sujeto} cruza hacia arriba ${objetivoSerie(condicion)}`
    case 'cruza_abajo':
      return `${sujeto} cruza hacia abajo ${objetivoSerie(condicion)}`
    case 'cruza_arriba_precio':
      return `el precio cruza hacia arriba ${articulo(serie)} ${serie} ${tf}`
    case 'cruza_abajo_precio':
      return `el precio cruza hacia abajo ${articulo(serie)} ${serie} ${tf}`
  }
}

function nombreSerie(
  indicador: string,
  serie: string,
  params?: Record<string, number>,
): string {
  if (indicador === 'ema' && params?.periodo) return `EMA ${params.periodo}`
  const info = INDICADORES_REGLAS[indicador]
  const etiqueta = info?.series.find(({ valor }) => valor === serie)?.etiqueta ?? serie
  // Series de nombre genérico dentro de su indicador: se les antepone el indicador
  if (etiqueta === 'media' || etiqueta === 'señal' || etiqueta === 'histograma') {
    return `${etiqueta} de ${info.etiqueta}`
  }
  return etiqueta
}

function articulo(nombre: string): string {
  const femeninas = ['banda', 'EMA', 'media', 'línea', 'señal']
  return femeninas.some((prefijo) => nombre.startsWith(prefijo)) ? 'la' : 'el'
}

function numero(condicion: CondicionRegla): string {
  if (typeof condicion.objetivo !== 'number') return '—'
  return String(condicion.objetivo).replace('-', '−')
}

function objetivoSerie(condicion: CondicionRegla): string {
  if (typeof condicion.objetivo === 'number') return numero(condicion)
  if (!condicion.objetivo) return '—'
  const nombre = nombreSerie(
    condicion.indicador,
    condicion.objetivo.serie,
    condicion.objetivo.params,
  )
  return `${articulo(nombre)} ${nombre}`
}
