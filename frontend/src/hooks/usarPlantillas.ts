import { useCallback, useEffect, useState } from 'react'
import { crearPlantilla, eliminarPlantilla, obtenerPlantillas } from '../api/cliente'
import type { Plantilla, PlantillaNueva } from '../api/tipos'

/** Plantillas de estrategia (predefinidas + propias) con alta y baja de las
 *  propias; recarga la lista tras cada cambio. */
export function usarPlantillas() {
  const [plantillas, setPlantillas] = useState<Plantilla[]>([])

  const cargar = useCallback(async () => {
    try {
      setPlantillas(await obtenerPlantillas())
    } catch {
      setPlantillas([])
    }
  }, [])

  useEffect(() => {
    void cargar()
  }, [cargar])

  const crear = useCallback(
    async (datos: PlantillaNueva) => {
      const nueva = await crearPlantilla(datos)
      await cargar()
      return nueva
    },
    [cargar],
  )

  const eliminar = useCallback(
    async (id: number) => {
      await eliminarPlantilla(id)
      await cargar()
    },
    [cargar],
  )

  return { plantillas, crear, eliminar }
}
