import { usarMoneda } from '../contextos/MonedaContext'
import { usarTicker } from '../contextos/TickerContext'
import { usarTickers } from './usarTickers'
import type { Moneda } from '../api/tipos'

export interface MonedaEfectiva {
  moneda: Moneda
  fija: boolean
}

/** Moneda con la que se muestra el ticker activo.
 *
 * CEDEARs (subyacente), índices y cripto cotizan en USD; los tickers de dólar
 * son tasas en ARS: en esos grupos la moneda queda fija y el toggle se
 * deshabilita. Panel Líder y General (BYMA) alternan ARS/USD normalmente. */
export function usarMonedaEfectiva(): MonedaEfectiva {
  const { moneda } = usarMoneda()
  const { ticker } = usarTicker()
  const paneles = usarTickers()

  if (paneles) {
    const siempreUSD = [...paneles.cedears, ...paneles.indices, ...paneles.cripto]
    if (siempreUSD.includes(ticker)) return { moneda: 'USD', fija: true }
    if (paneles.dolar.includes(ticker)) return { moneda: 'ARS', fija: true }
  }
  return { moneda, fija: false }
}
