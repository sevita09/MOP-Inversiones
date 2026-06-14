import { useEffect, useState } from 'react'
import { obtenerPrecios } from '../api/cliente'
import { usarMoneda } from '../contextos/MonedaContext'
import type { Precios } from '../api/tipos'

export function usarPrecios(): Precios {
  const { moneda } = usarMoneda()
  const [precios, setPrecios] = useState<Precios>({})

  useEffect(() => {
    let activo = true
    obtenerPrecios(moneda)
      .then((respuesta) => {
        if (activo) setPrecios(respuesta)
      })
      .catch(() => {
        // Conservar los precios previos: un fallo transitorio no borra las variaciones
      })
    return () => {
      activo = false
    }
  }, [moneda])

  return precios
}
