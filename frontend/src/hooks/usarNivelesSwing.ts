import { useEffect, useState } from 'react'
import { obtenerNivelesSwing, type NivelSwing } from '../api/cliente'
import type { Moneda, Temporalidad } from '../api/tipos'

// Niveles de soporte/resistencia. Solo consulta el backend con el toggle activo;
// con activo=false devuelve null (no dibuja ni pide datos).
export function usarNivelesSwing(
  ticker: string,
  temporalidad: Temporalidad,
  moneda: Moneda,
  activo: boolean,
): NivelSwing[] | null {
  const [datos, setDatos] = useState<NivelSwing[] | null>(null)

  useEffect(() => {
    if (!activo) {
      setDatos(null)
      return
    }
    let vigente = true
    obtenerNivelesSwing(ticker, temporalidad, moneda)
      .then((respuesta) => {
        if (vigente) setDatos(respuesta.niveles)
      })
      .catch(() => {
        if (vigente) setDatos(null)
      })

    return () => {
      vigente = false
    }
  }, [ticker, temporalidad, moneda, activo])

  return datos
}
