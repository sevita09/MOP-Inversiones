import { useEffect, useState } from 'react'
import { obtenerActualizacion } from '../api/cliente'
import type { EstadoActualizacion } from '../api/tipos'

export function usarActualizacion(): EstadoActualizacion | null {
  const [estado, setEstado] = useState<EstadoActualizacion | null>(null)

  useEffect(() => {
    let activo = true
    obtenerActualizacion()
      .then((respuesta) => {
        if (activo) setEstado(respuesta)
      })
      .catch(() => {
        // Sin red o backend caído: simplemente no se muestra el aviso
      })
    return () => {
      activo = false
    }
  }, [])

  return estado
}
