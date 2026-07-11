import { useEffect, useMemo, useState } from 'react'
import { obtenerIndicadores } from '../api/cliente'
import { usarRefrescoDatos } from './usarEstadoSync'
import { usarEstilos } from '../contextos/EstilosContext'
import { paramsQueryDe } from '../componentes/grafico/config/paramsIndicadores'
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
  const refresco = usarRefrescoDatos()
  const { paramsDe } = usarEstilos()
  const params = useMemo(
    () => paramsQueryDe(nombre, paramsDe(nombre), temporalidad),
    [paramsDe, nombre, temporalidad],
  )

  useEffect(() => {
    if (!activo) {
      setDatos(null)
      return
    }
    let vigente = true
    obtenerIndicadores(ticker, temporalidad, moneda, nombre, params)
      .then((respuesta) => {
        if (vigente) setDatos({ ts: respuesta.ts, series: respuesta.indicadores[nombre] })
      })
      .catch(() => {
        if (vigente) setDatos(null)
      })

    return () => {
      vigente = false
    }
  }, [ticker, temporalidad, moneda, nombre, activo, refresco, params])

  return datos
}
