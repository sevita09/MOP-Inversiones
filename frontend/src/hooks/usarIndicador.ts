import { useEffect, useState } from 'react'
import { obtenerIndicadores } from '../api/cliente'
import type { Moneda, SerieIndicador, Temporalidad } from '../api/tipos'

export interface DatosIndicador {
  ts: number[]
  series: Record<string, SerieIndicador>
}

// Trae un indicador del backend solo cuando su panel está activo. Con activo=false
// devuelve null (no dibuja ni consulta). Genérico: sirve para macd, rsi, estocástico.
export function usarIndicador(
  ticker: string,
  temporalidad: Temporalidad,
  moneda: Moneda,
  nombre: string,
  activo: boolean,
): DatosIndicador | null {
  const [datos, setDatos] = useState<DatosIndicador | null>(null)

  useEffect(() => {
    if (!activo) {
      setDatos(null)
      return
    }
    let vigente = true
    obtenerIndicadores(ticker, temporalidad, moneda, nombre)
      .then((respuesta) => {
        if (vigente) setDatos({ ts: respuesta.ts, series: respuesta.indicadores[nombre] })
      })
      .catch(() => {
        if (vigente) setDatos(null)
      })

    return () => {
      vigente = false
    }
  }, [ticker, temporalidad, moneda, nombre, activo])

  return datos
}
