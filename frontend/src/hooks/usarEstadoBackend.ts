import { useEffect, useState } from 'react'
import { obtenerJson } from '../api/cliente'
import { proximoIntervaloMs } from './usarEstadoSync'
import type { EstadoSalud } from '../api/tipos'

export type ConexionBackend = 'verificando' | 'conectado' | 'sin_conexion'

export function usarEstadoBackend(): ConexionBackend {
  const [conexion, setConexion] = useState<ConexionBackend>('verificando')

  useEffect(() => {
    let activo = true

    const verificar = () => {
      obtenerJson<EstadoSalud>('/api/salud')
        .then((salud) => {
          if (activo) setConexion(salud.estado === 'ok' ? 'conectado' : 'sin_conexion')
        })
        .catch(() => {
          if (activo) setConexion('sin_conexion')
        })
    }

    let timer: ReturnType<typeof setTimeout>
    const programar = () => {
      timer = setTimeout(() => {
        verificar()
        programar()
      }, proximoIntervaloMs())
    }

    verificar()
    programar()
    return () => {
      activo = false
      clearTimeout(timer)
    }
  }, [])

  return conexion
}
