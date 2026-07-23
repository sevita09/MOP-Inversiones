import { useCallback, useEffect, useState } from 'react'
import {
  eliminarSenal,
  eliminarSenalesVencidas,
  marcarSenalesVistas,
  obtenerSenales,
} from '../api/cliente'
import type { Senal } from '../api/tipos'
import { usarRefrescoDatos } from './usarEstadoSync'

// Se dispara al marcar las señales como vistas: el badge de la navegación lo
// escucha para apagarse sin esperar al próximo sync.
export const EVENTO_SENALES = 'mop:senales-vistas'

/** Lista de señales + cuántas sin ver, para la página. Se refresca con cada
 *  sincronización del backend. `marcarVistas` apaga el badge. */
export function usarSenales() {
  const [senales, setSenales] = useState<Senal[]>([])
  const [sinVer, setSinVer] = useState(0)
  const [cargando, setCargando] = useState(true)
  const refresco = usarRefrescoDatos()

  const cargar = useCallback(async () => {
    try {
      const respuesta = await obtenerSenales()
      setSenales(respuesta.senales)
      setSinVer(respuesta.sin_ver)
    } catch {
      // deja lo previo: un fallo transitorio no vacía la lista
    } finally {
      setCargando(false)
    }
  }, [])

  useEffect(() => {
    void cargar()
  }, [cargar, refresco])

  const marcarVistas = useCallback(async () => {
    await marcarSenalesVistas()
    setSinVer(0)
    setSenales((previas) => previas.map((s) => ({ ...s, vista: true })))
    window.dispatchEvent(new Event(EVENTO_SENALES))
  }, [])

  const eliminar = useCallback(
    async (id: number) => {
      await eliminarSenal(id)
      await cargar()
      window.dispatchEvent(new Event(EVENTO_SENALES))
    },
    [cargar],
  )

  const eliminarVencidas = useCallback(async () => {
    await eliminarSenalesVencidas()
    await cargar()
    window.dispatchEvent(new Event(EVENTO_SENALES))
  }, [cargar])

  return { senales, sinVer, cargando, marcarVistas, eliminar, eliminarVencidas }
}

/** Solo el contador sin ver, para el badge de la navegación. */
export function usarSenalesSinVer(): number {
  const [sinVer, setSinVer] = useState(0)
  const refresco = usarRefrescoDatos()

  useEffect(() => {
    let activo = true
    const cargar = () =>
      obtenerSenales()
        .then((r) => {
          if (activo) setSinVer(r.sin_ver)
        })
        .catch(() => {})
    void cargar()
    window.addEventListener(EVENTO_SENALES, cargar)
    return () => {
      activo = false
      window.removeEventListener(EVENTO_SENALES, cargar)
    }
  }, [refresco])

  return sinVer
}
