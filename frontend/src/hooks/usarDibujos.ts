import { useCallback, useEffect, useRef, useState } from 'react'
import {
  obtenerDibujos,
  crearDibujo,
  actualizarDibujo,
  eliminarDibujo,
  type Dibujo,
} from '../api/cliente'

export function usarDibujos(ticker: string) {
  const [dibujos, setDibujos] = useState<Dibujo[]>([])
  const tickerRef = useRef(ticker)
  tickerRef.current = ticker

  useEffect(() => {
    let cancelado = false
    obtenerDibujos(ticker).then((d) => {
      if (!cancelado) setDibujos(d)
    }).catch(() => {
      if (!cancelado) setDibujos([])
    })
    return () => { cancelado = true }
  }, [ticker])

  const agregar = useCallback(async (tipo: string, datos: Record<string, unknown>) => {
    const nuevo = await crearDibujo(tickerRef.current, tipo, datos)
    setDibujos((prev) => [...prev, nuevo])
    return nuevo
  }, [])

  const actualizar = useCallback(async (id: number, datos: Record<string, unknown>) => {
    await actualizarDibujo(id, datos)
    setDibujos((prev) => prev.map((d) => (d.id === id ? { ...d, datos } : d)))
  }, [])

  const eliminar = useCallback(async (id: number) => {
    await eliminarDibujo(id)
    setDibujos((prev) => prev.filter((d) => d.id !== id))
  }, [])

  return { dibujos, agregar, actualizar, eliminar }
}
