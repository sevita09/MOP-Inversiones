import { useEffect, useState } from 'react'
import { obtenerVelas } from '../api/cliente'
import { usarRefrescoDatos } from './usarEstadoSync'
import type { InfoAdr, Moneda, Temporalidad, Vela } from '../api/tipos'

interface EstadoVelas {
  velas: Vela[]
  adr: InfoAdr | null
  cargando: boolean
  error: string | null
}

export function usarVelas(
  ticker: string,
  temporalidad: Temporalidad,
  moneda: Moneda,
): EstadoVelas {
  const [estado, setEstado] = useState<EstadoVelas>({
    velas: [],
    adr: null,
    cargando: true,
    error: null,
  })
  const refresco = usarRefrescoDatos()

  useEffect(() => {
    let activo = true
    // Refresco por sync: sin spinner, el gráfico se actualiza en el lugar
    setEstado((previo) => ({ ...previo, cargando: previo.velas.length === 0, error: null }))

    obtenerVelas(ticker, temporalidad, moneda)
      .then((respuesta) => {
        if (activo)
          setEstado({ velas: respuesta.velas, adr: respuesta.adr, cargando: false, error: null })
      })
      .catch((err: unknown) => {
        if (activo) {
          const mensaje = err instanceof Error ? err.message : 'Error al cargar velas'
          // Conservar las velas previas: un fallo transitorio no borra el gráfico
          setEstado((previo) => ({ ...previo, cargando: false, error: mensaje }))
        }
      })

    return () => {
      activo = false
    }
  }, [ticker, temporalidad, moneda, refresco])

  return estado
}
