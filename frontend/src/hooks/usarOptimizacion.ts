import { useCallback, useEffect, useRef, useState } from 'react'
import { lanzarOptimizacion, obtenerEstadoOptimizacion } from '../api/cliente'
import type {
  EstadoOptimizacion,
  MetricaOptimizacion,
  ParametroOptimizacion,
} from '../api/tipos'

const INTERVALO_MS = 500

const INICIAL: EstadoOptimizacion = {
  en_curso: false,
  bot_id: null,
  hechos: 0,
  total: 0,
  resultado: null,
  error: null,
}

/** Lanza la optimización y sigue su progreso hasta que termina. */
export function usarOptimizacion() {
  const [estado, setEstado] = useState<EstadoOptimizacion>(INICIAL)
  const [mensaje, setMensaje] = useState('')
  const timer = useRef<ReturnType<typeof setTimeout> | null>(null)

  const detenerPolling = () => {
    if (timer.current) clearTimeout(timer.current)
    timer.current = null
  }

  const consultar = useCallback(async () => {
    try {
      const actual = await obtenerEstadoOptimizacion()
      setEstado(actual)
      // Mientras corre, volver a preguntar; al terminar, dejar de consultar
      if (actual.en_curso) timer.current = setTimeout(() => void consultar(), INTERVALO_MS)
    } catch {
      detenerPolling()
    }
  }, [])

  // Limpiar el timer si el componente se desmonta a mitad de una corrida
  useEffect(() => detenerPolling, [])

  const optimizar = useCallback(
    async (
      idBot: number,
      parametros: ParametroOptimizacion[],
      metrica: MetricaOptimizacion,
    ) => {
      setMensaje('')
      setEstado({ ...INICIAL, en_curso: true })
      try {
        await lanzarOptimizacion(idBot, parametros, metrica)
        void consultar()
      } catch (error) {
        const texto = error instanceof Error ? error.message : ''
        setMensaje(
          texto.includes('409')
            ? 'Ya hay una optimización corriendo'
            : 'No se pudo lanzar la optimización (revisá los rangos)',
        )
        setEstado(INICIAL)
      }
    },
    [consultar],
  )

  return { estado, mensaje, optimizar }
}
