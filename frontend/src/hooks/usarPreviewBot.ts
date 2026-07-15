import { useEffect, useState } from 'react'
import { previewBot } from '../api/cliente'
import type { Moneda, ReglasBot, RespuestaPreview, TemporalidadBot } from '../api/tipos'
import { reglasConContenido } from '../componentes/bots/configReglas'

const SIN_SENALES: RespuestaPreview = { ts_entrada: [], ts_salida: [] }
const DEBOUNCE_MS = 500

/** Señales de la vista previa, recalculadas solas al editar (con debounce):
 *  cada tecleo en el constructor reprograma la consulta 500 ms para adelante. */
export function usarPreviewBot(
  ticker: string,
  temporalidad: TemporalidadBot,
  moneda: Moneda,
  reglas: ReglasBot,
): RespuestaPreview {
  const [senales, setSenales] = useState<RespuestaPreview>(SIN_SENALES)

  useEffect(() => {
    if (!ticker || !reglasConContenido(reglas)) {
      setSenales(SIN_SENALES)
      return
    }
    let activo = true
    const timer = setTimeout(() => {
      previewBot(ticker, temporalidad, moneda, reglas)
        .then((respuesta) => {
          if (activo) setSenales(respuesta)
        })
        .catch(() => {
          // Una regla a medio editar puede ser inválida: no hay señales y ya
          if (activo) setSenales(SIN_SENALES)
        })
    }, DEBOUNCE_MS)
    return () => {
      activo = false
      clearTimeout(timer)
    }
  }, [ticker, temporalidad, moneda, reglas])

  return senales
}
