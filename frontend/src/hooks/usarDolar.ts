import { useEffect, useState } from 'react'
import { obtenerDolar } from '../api/cliente'
import type { RespuestaDolar } from '../api/tipos'

export function usarDolar(): RespuestaDolar | null {
  const [dolar, setDolar] = useState<RespuestaDolar | null>(null)

  useEffect(() => {
    let activo = true
    obtenerDolar()
      .then((respuesta) => {
        if (activo) setDolar(respuesta)
      })
      .catch(() => {
        // Conservar la cotización previa ante un fallo transitorio
      })
    return () => {
      activo = false
    }
  }, [])

  return dolar
}
