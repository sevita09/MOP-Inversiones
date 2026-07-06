import { useEffect, useState } from 'react'
import { obtenerVersion } from '../api/cliente'

export interface VersionApp {
  version: string | null
  canal: string
}

/** Versión y canal ("prod"/"dev") del backend que sirve la app. */
export function usarVersion(): VersionApp {
  const [datos, setDatos] = useState<VersionApp>({ version: null, canal: 'prod' })

  useEffect(() => {
    let activo = true
    obtenerVersion()
      .then(({ version, canal }) => {
        if (activo) setDatos({ version, canal: canal || 'prod' })
      })
      .catch(() => {
        // Sin backend: sin versión, se asume prod
      })
    return () => {
      activo = false
    }
  }, [])

  return datos
}
