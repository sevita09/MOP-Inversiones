import { useEffect, useState } from 'react'
import { obtenerLotes } from '../api/cliente'
import type { LotesDeTicker, Moneda } from '../api/tipos'
import { usarRefrescoDatos } from './usarEstadoSync'

const VACIO: LotesDeTicker = { ticker: '', moneda: 'ARS', lotes: [], ppc: null, cantidad: 0 }

/** Compras abiertas del papel (FIFO) para marcarlas sobre el gráfico.
 *  Solo consulta cuando la vista está activa: sin tenencia no molesta al backend. */
export function usarLotesCartera(
  ticker: string,
  moneda: Moneda,
  activo: boolean,
): LotesDeTicker {
  const [lotes, setLotes] = useState<LotesDeTicker>(VACIO)
  const refresco = usarRefrescoDatos()

  useEffect(() => {
    if (!activo || !ticker) {
      setLotes(VACIO)
      return
    }
    let vigente = true
    obtenerLotes(ticker, moneda)
      .then((datos) => vigente && setLotes(datos))
      .catch(() => vigente && setLotes(VACIO))
    return () => {
      vigente = false
    }
  }, [ticker, moneda, activo, refresco])

  return lotes
}
