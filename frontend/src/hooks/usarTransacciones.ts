import { useCallback, useEffect, useState } from 'react'
import {
  crearTransaccion,
  editarTransaccion,
  eliminarTransaccion,
  obtenerTransacciones,
} from '../api/cliente'
import type { Transaccion, TransaccionNueva } from '../api/tipos'

/** Historial de operaciones con las acciones del CRUD; recarga tras cada cambio. */
export function usarTransacciones(ticker?: string) {
  const [transacciones, setTransacciones] = useState<Transaccion[]>([])
  const [cargando, setCargando] = useState(true)

  const cargar = useCallback(async () => {
    try {
      setTransacciones(await obtenerTransacciones(ticker))
    } catch {
      setTransacciones([])
    } finally {
      setCargando(false)
    }
  }, [ticker])

  useEffect(() => {
    void cargar()
  }, [cargar])

  const crear = useCallback(
    async (datos: TransaccionNueva) => {
      const creada = await crearTransaccion(datos)
      await cargar()
      return creada
    },
    [cargar],
  )

  const editar = useCallback(
    async (id: number, cambios: Partial<TransaccionNueva>) => {
      const editada = await editarTransaccion(id, cambios)
      await cargar()
      return editada
    },
    [cargar],
  )

  const eliminar = useCallback(
    async (id: number) => {
      await eliminarTransaccion(id)
      await cargar()
    },
    [cargar],
  )

  return { transacciones, cargando, crear, editar, eliminar }
}
