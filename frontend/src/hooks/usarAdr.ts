import { useEffect, useState } from 'react'
import { obtenerAdr } from '../api/cliente'
import type { InfoAdr } from '../api/tipos'

/** Info del ADR de una acción (o null si no tiene). Es estático por ticker. */
export function usarAdr(ticker: string): InfoAdr | null {
  const [adr, setAdr] = useState<InfoAdr | null>(null)

  useEffect(() => {
    let activo = true
    obtenerAdr(ticker)
      .then(({ adr }) => {
        if (activo) setAdr(adr)
      })
      .catch(() => {
        if (activo) setAdr(null)
      })
    return () => {
      activo = false
    }
  }, [ticker])

  return adr
}
