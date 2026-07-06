import { useEffect, useState } from 'react'
import { obtenerActualizacion } from '../api/cliente'
import { proximoIntervaloMs } from './usarEstadoSync'
import type { EstadoActualizacion } from '../api/tipos'

export function usarActualizacion(): EstadoActualizacion | null {
  const [estado, setEstado] = useState<EstadoActualizacion | null>(null)

  useEffect(() => {
    let activo = true

    const consultar = () => {
      obtenerActualizacion()
        .then((respuesta) => {
          if (activo) setEstado(respuesta)
        })
        .catch(() => {
          // Sin red o backend caído: simplemente no se muestra el aviso
        })
    }

    let timer: ReturnType<typeof setTimeout>
    const programar = () => {
      timer = setTimeout(() => {
        consultar()
        programar()
      }, proximoIntervaloMs())
    }

    // Se re-chequea con la app abierta: si sale una versión nueva, la pill aparece sola
    consultar()
    programar()
    return () => {
      activo = false
      clearTimeout(timer)
    }
  }, [])

  return estado
}
