import { useEffect, useRef, useState } from 'react'
import { obtenerEstadoSync } from '../api/cliente'

// Se dispara cuando el backend terminó una sincronización nueva: los hooks de
// datos (velas, precios, indicadores) lo escuchan y se refrescan solos.
export const EVENTO_DATOS = 'mop:datos-actualizados'

const DIEZ_SEG = 10 * 1000
const QUINCE_MIN = 15 * 60 * 1000
const UNA_HORA = 60 * 60 * 1000

/** Misma regla que el backend: rueda = lunes a viernes de 9 a 18, hora argentina. */
export function enRueda(): boolean {
  const partes = new Intl.DateTimeFormat('en-US', {
    timeZone: 'America/Argentina/Buenos_Aires',
    weekday: 'short',
    hour: 'numeric',
    hour12: false,
  }).formatToParts(new Date())
  const dia = partes.find((p) => p.type === 'weekday')?.value ?? ''
  const hora = Number(partes.find((p) => p.type === 'hour')?.value ?? '0')
  return !['Sat', 'Sun'].includes(dia) && hora >= 9 && hora < 18
}

/** Cadencia de consultas al backend: 15 min en rueda, 1 hora fuera. */
export function proximoIntervaloMs(): number {
  return enRueda() ? QUINCE_MIN : UNA_HORA
}

export interface EstadoSync {
  enCurso: boolean
  ultimaSync: string | null
}

/** Consulta el estado del sync (15 min en rueda, 1 h fuera) y avisa cuando hay datos nuevos. */
export function usarEstadoSync(): EstadoSync {
  const [estado, setEstado] = useState<EstadoSync>({ enCurso: false, ultimaSync: null })
  const previa = useRef<string | null>(null)

  useEffect(() => {
    let activo = true
    let timer: ReturnType<typeof setTimeout>

    const consultar = () => {
      obtenerEstadoSync()
        .then(({ en_curso, ultima_sync }) => {
          if (!activo) return
          setEstado({ enCurso: en_curso, ultimaSync: ultima_sync })
          if (previa.current !== null && ultima_sync && ultima_sync !== previa.current) {
            window.dispatchEvent(new Event(EVENTO_DATOS))
          }
          previa.current = ultima_sync
          // Con un sync en curso, mirar seguido hasta verlo terminar;
          // en reposo rige la cadencia de la rueda
          timer = setTimeout(consultar, en_curso ? DIEZ_SEG : proximoIntervaloMs())
        })
        .catch(() => {
          // Backend caído: lo informa usarEstadoBackend; reintentar con la cadencia normal
          if (activo) timer = setTimeout(consultar, proximoIntervaloMs())
        })
    }

    consultar()
    return () => {
      activo = false
      clearTimeout(timer)
    }
  }, [])

  return estado
}

/** Contador que se incrementa con cada sincronización nueva del backend.
 *  Sumarlo a las dependencias de un efecto lo re-ejecuta con datos frescos. */
export function usarRefrescoDatos(): number {
  const [refresco, setRefresco] = useState(0)

  useEffect(() => {
    const alActualizarse = () => setRefresco((previo) => previo + 1)
    window.addEventListener(EVENTO_DATOS, alActualizarse)
    return () => window.removeEventListener(EVENTO_DATOS, alActualizarse)
  }, [])

  return refresco
}
