import { useEffect, useMemo, useState } from 'react'
import { obtenerIndicadores } from '../api/cliente'
import { usarEstilos } from '../contextos/EstilosContext'
import { paramsQueryDe } from '../componentes/grafico/config/paramsIndicadores'
import type { Moneda, SerieIndicador, Temporalidad } from '../api/tipos'

export interface DatosBollinger {
  ts: number[]
  series: Record<string, SerieIndicador>
}

// Bandas de Bollinger (SMA 20 ± 2σ). Solo pide datos con el toggle activo.
export function usarBollinger(
  ticker: string,
  temporalidad: Temporalidad,
  moneda: Moneda,
  activo: boolean,
): DatosBollinger | null {
  const [datos, setDatos] = useState<DatosBollinger | null>(null)
  const { paramsDe } = usarEstilos()
  const params = useMemo(
    () => paramsQueryDe('bollinger', paramsDe('bollinger'), temporalidad),
    [paramsDe, temporalidad],
  )

  useEffect(() => {
    if (!activo) {
      setDatos(null)
      return
    }
    let vigente = true
    obtenerIndicadores(ticker, temporalidad, moneda, 'bollinger', params)
      .then((respuesta) => {
        if (vigente) setDatos({ ts: respuesta.ts, series: respuesta.indicadores.bollinger })
      })
      .catch(() => {
        if (vigente) setDatos(null)
      })

    return () => {
      vigente = false
    }
  }, [ticker, temporalidad, moneda, activo, params])

  return datos
}
