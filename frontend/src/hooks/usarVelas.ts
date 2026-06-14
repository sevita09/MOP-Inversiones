import { useEffect, useState } from 'react'
import { obtenerVelas } from '../api/cliente'
import type { Moneda, Temporalidad, Vela } from '../api/tipos'

interface EstadoVelas {
  velas: Vela[]
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
    cargando: true,
    error: null,
  })

  useEffect(() => {
    let activo = true
    setEstado((previo) => ({ ...previo, cargando: true, error: null }))

    obtenerVelas(ticker, temporalidad, moneda)
      .then((respuesta) => {
        if (activo) setEstado({ velas: respuesta.velas, cargando: false, error: null })
      })
      .catch((err: unknown) => {
        if (activo) {
          const mensaje = err instanceof Error ? err.message : 'Error al cargar velas'
          // Conservar las velas previas: un fallo transitorio no borra el gráfico
          setEstado((previo) => ({ velas: previo.velas, cargando: false, error: mensaje }))
        }
      })

    return () => {
      activo = false
    }
  }, [ticker, temporalidad, moneda])

  return estado
}
