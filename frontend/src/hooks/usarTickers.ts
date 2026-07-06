import { useCallback, useEffect, useState } from 'react'
import { obtenerTickers } from '../api/cliente'
import type { Paneles } from '../api/tipos'

// Evento para refrescar la lista cuando se agrega un ticker nuevo
export const EVENTO_TICKERS = 'mop:tickers-actualizados'

export function usarTickers(): Paneles | null {
  const [paneles, setPaneles] = useState<Paneles | null>(null)

  const cargar = useCallback(() => {
    obtenerTickers()
      .then(setPaneles)
      .catch(() => setPaneles(null))
  }, [])

  useEffect(() => {
    cargar()
    window.addEventListener(EVENTO_TICKERS, cargar)
    return () => window.removeEventListener(EVENTO_TICKERS, cargar)
  }, [cargar])

  return paneles
}
