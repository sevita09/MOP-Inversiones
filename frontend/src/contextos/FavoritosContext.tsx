import {
  createContext,
  useCallback,
  useContext,
  useMemo,
  useState,
  type ReactNode,
} from 'react'

interface ContextoFavoritos {
  favoritos: string[]
  alternar: (simbolo: string) => void
  esFavorito: (simbolo: string) => boolean
}

const CLAVE_ALMACEN = 'mop.favoritos'

const Contexto = createContext<ContextoFavoritos | null>(null)

function leerFavoritos(): string[] {
  try {
    const crudo = localStorage.getItem(CLAVE_ALMACEN)
    return crudo ? (JSON.parse(crudo) as string[]) : []
  } catch {
    return []
  }
}

export function ProveedorFavoritos({ children }: { children: ReactNode }) {
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

  const valor = useMemo<ContextoFavoritos>(
    () => ({ favoritos, alternar, esFavorito }),
    [favoritos, alternar, esFavorito],
  )

  return <Contexto.Provider value={valor}>{children}</Contexto.Provider>
}

export function usarFavoritos(): ContextoFavoritos {
  const contexto = useContext(Contexto)
  if (contexto === null) {
    throw new Error('usarFavoritos debe usarse dentro de ProveedorFavoritos')
  }
  return contexto
}
