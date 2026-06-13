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
        if (activo) setDolar(null)
      })
    return () => {
      activo = false
    }
  }, [])

  return dolar
}
