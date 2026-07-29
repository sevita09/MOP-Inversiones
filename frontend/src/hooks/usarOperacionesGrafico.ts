import { useEffect, useState } from 'react'
import { obtenerOperacionesGrafico } from '../api/cliente'
import type { Moneda, OperacionGrafico } from '../api/tipos'
import { usarRefrescoDatos } from './usarEstadoSync'

/** Operaciones propias del papel para marcarlas sobre el gráfico.
 *  Solo consulta con la vista activa: si el toggle está apagado no molesta. */
export function usarOperacionesGrafico(
  ticker: string,
  moneda: Moneda,
  activo: boolean,
): OperacionGrafico[] {
  const [operaciones, setOperaciones] = useState<OperacionGrafico[]>([])
  const refresco = usarRefrescoDatos()

  useEffect(() => {
    if (!activo || !ticker) {
      setOperaciones([])
      return
    }
    let vigente = true
    obtenerOperacionesGrafico(ticker, moneda)
      .then((datos) => vigente && setOperaciones(datos.operaciones))
      .catch(() => vigente && setOperaciones([]))
    return () => {
      vigente = false
    }
  }, [ticker, moneda, activo, refresco])

  return operaciones
}
