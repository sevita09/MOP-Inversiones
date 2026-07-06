import { useEffect, useState } from 'react'
import { obtenerVersion } from '../api/cliente'

/** Canal de la app que sirve el backend: "prod" o "dev" (la app de pruebas). */
export function usarCanal(): string {
  const [canal, setCanal] = useState('prod')

  useEffect(() => {
    let activo = true
    obtenerVersion()
      .then(({ canal }) => {
        if (activo && canal) setCanal(canal)
      })
      .catch(() => {
        // Sin backend: se asume prod
      })
    return () => {
      activo = false
    }
  }, [])

  return canal
}
