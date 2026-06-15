import { useEffect, useState } from 'react'
import { obtenerIndicadores } from '../api/cliente'
import type { Moneda, SerieIndicador, Temporalidad } from '../api/tipos'

export interface DatosBandas {
  ts: number[]
  series: Record<string, SerieIndicador>
}

// EMA central + bandas σ. Solo pide datos cuando el toggle está activo;
// con activo=false devuelve null (no dibuja ni consulta el backend).
export function usarBandas(
  ticker: string,
  temporalidad: Temporalidad,
  moneda: Moneda,
  activo: boolean,
): DatosBandas | null {
  const [datos, setDatos] = useState<DatosBandas | null>(null)

  useEffect(() => {
    if (!activo) {
      setDatos(null)
      return
    }
    let vigente = true
    obtenerIndicadores(ticker, temporalidad, moneda, 'bandas')
      .then((respuesta) => {
        if (vigente) setDatos({ ts: respuesta.ts, series: respuesta.indicadores.bandas })
      })
      .catch(() => {
        // Un fallo deja las bandas sin datos; el precio sigue mostrándose
        if (vigente) setDatos(null)
      })

    return () => {
      vigente = false
    }
  }, [ticker, temporalidad, moneda, activo])

  return datos
}
