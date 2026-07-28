import { usarMoneda } from '../contextos/MonedaContext'
import { usarTicker } from '../contextos/TickerContext'
import { usarTickers } from './usarTickers'
import type { Moneda } from '../api/tipos'

export interface MonedaEfectiva {
  moneda: Moneda
  fija: boolean
}

/** Índices de la rueda local: cotizan en ARS y alternan como cualquier BYMA
 * (el "Merval en dólares" sale de convertirlos con el CCL). */
const INDICES_LOCALES = ['MERVAL']

/** Moneda con la que se muestra el ticker activo.
 *
 * CEDEARs (subyacente), índices del exterior y cripto cotizan en USD; los
 * tickers de dólar son tasas en ARS: en esos grupos la moneda queda fija y el
 * toggle se deshabilita. Panel Líder, General (BYMA) y los índices locales
 * alternan ARS/USD normalmente. */
export function usarMonedaEfectiva(): MonedaEfectiva {
  const { moneda } = usarMoneda()
  const { ticker } = usarTicker()
  const paneles = usarTickers()

  if (paneles) {
    const indicesExtranjeros = paneles.indices.filter((t) => !INDICES_LOCALES.includes(t))
    const siempreUSD = [...paneles.cedears, ...indicesExtranjeros, ...paneles.cripto]
    if (siempreUSD.includes(ticker)) return { moneda: 'USD', fija: true }
    if (paneles.dolar.includes(ticker)) return { moneda: 'ARS', fija: true }
  }
  return { moneda, fija: false }
}
