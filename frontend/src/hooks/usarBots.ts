import { useCallback, useEffect, useState } from 'react'
import {
  crearBot,
  duplicarBot,
  editarBot,
  eliminarBot,
  obtenerBots,
} from '../api/cliente'
import type { Bot, BotNuevo } from '../api/tipos'

/** Lista de bots con las acciones del CRUD; recarga tras cada mutación. */
export function usarBots() {
  const [bots, setBots] = useState<Bot[]>([])
  const [cargando, setCargando] = useState(true)

  const cargar = useCallback(async () => {
    try {
      setBots(await obtenerBots())
    } catch {
      setBots([])
    } finally {
      setCargando(false)
    }
  }, [])

  useEffect(() => {
    void cargar()
  }, [cargar])

  const crear = useCallback(
    async (datos: BotNuevo) => {
      const bot = await crearBot(datos)
      await cargar()
      return bot
    },
    [cargar],
  )

  const editar = useCallback(
    async (id: number, cambios: Partial<BotNuevo> & { activo?: boolean }) => {
      const bot = await editarBot(id, cambios)
      await cargar()
      return bot
    },
    [cargar],
  )

  const eliminar = useCallback(
    async (id: number) => {
      await eliminarBot(id)
      await cargar()
    },
    [cargar],
  )

  const duplicar = useCallback(
    async (id: number) => {
      await duplicarBot(id)
      await cargar()
    },
    [cargar],
  )

  const alternarActivo = useCallback(
    async (bot: Bot) => {
      await editarBot(bot.id, { activo: !bot.activo })
      await cargar()
    },
    [cargar],
  )

  return { bots, cargando, crear, editar, eliminar, duplicar, alternarActivo }
}
