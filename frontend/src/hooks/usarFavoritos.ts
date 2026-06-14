import { useCallback, useState } from 'react'

const CLAVE_ALMACEN = 'mop.favoritos'

function leerFavoritos(): string[] {
  try {
    const crudo = localStorage.getItem(CLAVE_ALMACEN)
    return crudo ? (JSON.parse(crudo) as string[]) : []
  } catch {
    return []
  }
}

export function usarFavoritos() {
  const [favoritos, setFavoritos] = useState<string[]>(leerFavoritos)

  const alternar = useCallback((simbolo: string) => {
    setFavoritos((previos) => {
      const siguientes = previos.includes(simbolo)
        ? previos.filter((s) => s !== simbolo)
        : [...previos, simbolo]
      localStorage.setItem(CLAVE_ALMACEN, JSON.stringify(siguientes))
      return siguientes
    })
  }, [])

  const esFavorito = useCallback(
    (simbolo: string) => favoritos.includes(simbolo),
    [favoritos],
  )

  return { favoritos, alternar, esFavorito }
}
