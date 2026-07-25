import { useCallback, useEffect, useState } from 'react'
import {
  crearPresetRiesgo,
  eliminarPresetRiesgo,
  obtenerPresetsRiesgo,
} from '../api/cliente'
import type { PresetRiesgo, RiesgoBot } from '../api/tipos'

/** Presets de gestión de riesgo guardados, con alta y baja; recarga tras cada cambio. */
export function usarPresetsRiesgo() {
  const [presets, setPresets] = useState<PresetRiesgo[]>([])

  const cargar = useCallback(async () => {
    try {
      setPresets(await obtenerPresetsRiesgo())
    } catch {
      setPresets([])
    }
  }, [])

  useEffect(() => {
    void cargar()
  }, [cargar])

  const crear = useCallback(
    async (nombre: string, riesgo: RiesgoBot) => {
      const preset = await crearPresetRiesgo(nombre, riesgo)
      await cargar()
      return preset
    },
    [cargar],
  )

  const eliminar = useCallback(
    async (id: number) => {
      await eliminarPresetRiesgo(id)
      await cargar()
    },
    [cargar],
  )

  return { presets, crear, eliminar }
}
