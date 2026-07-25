import { useCallback, useEffect, useState } from 'react'
import { obtenerBacktest } from '../api/cliente'
import type { ResultadoBacktest } from '../api/tipos'

// Ventanas de análisis; null = toda la historia disponible
export const VENTANAS: { etiqueta: string; meses: number | null }[] = [
  { etiqueta: '1A', meses: 12 },
  { etiqueta: '3A', meses: 36 },
  { etiqueta: '5A', meses: 60 },
  { etiqueta: 'Todo', meses: null },
]

function desdeDeMeses(meses: number | null): number | undefined {
  if (meses === null) return undefined
  const fecha = new Date()
  fecha.setMonth(fecha.getMonth() - meses)
  return Math.floor(fecha.getTime() / 1000)
}

/** Corre el backtest de un bot y lo re-corre al cambiar la ventana. */
export function usarBacktest(idBot: number | null, meses: number | null) {
  const [resultado, setResultado] = useState<ResultadoBacktest | null>(null)
  const [cargando, setCargando] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const cargar = useCallback(async () => {
    if (idBot === null) return
    setCargando(true)
    setError(null)
    try {
      setResultado(await obtenerBacktest(idBot, desdeDeMeses(meses)))
    } catch (err) {
      const texto = err instanceof Error ? err.message : ''
      setError(
        texto.includes('422')
          ? 'El bot no tiene reglas de entrada para backtestear'
          : 'No se pudo correr el backtest',
      )
      setResultado(null)
    } finally {
      setCargando(false)
    }
  }, [idBot, meses])

  useEffect(() => {
    void cargar()
  }, [cargar])

  return { resultado, cargando, error, recargar: cargar }
}
