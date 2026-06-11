import { useEffect, useState } from 'react'
import { obtenerJson } from '../api/cliente'
import type { EstadoSalud } from '../api/tipos'

export type ConexionBackend = 'verificando' | 'conectado' | 'sin_conexion'

export function usarEstadoBackend(): ConexionBackend {
  const [conexion, setConexion] = useState<ConexionBackend>('verificando')

  useEffect(() => {
    let activo = true
    obtenerJson<EstadoSalud>('/api/salud')
      .then((salud) => {
        if (activo) setConexion(salud.estado === 'ok' ? 'conectado' : 'sin_conexion')
      })
      .catch(() => {
        if (activo) setConexion('sin_conexion')
      })
    return () => {
      activo = false
    }
  }, [])

  return conexion
}
