import { useEffect, useState } from 'react'
import { obtenerTickers } from '../api/cliente'
import type { Paneles } from '../api/tipos'

export function usarTickers(): Paneles | null {
  const [paneles, setPaneles] = useState<Paneles | null>(null)

  useEffect(() => {
    let activo = true
    obtenerTickers()
      .then((respuesta) => {
        if (activo) setPaneles(respuesta)
      })
      .catch(() => {
        if (activo) setPaneles(null)
      })
    return () => {
      activo = false
    }
  }, [])

  return paneles
}
