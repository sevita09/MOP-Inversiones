import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from 'react'
import { guardarFavoritos, obtenerFavoritos } from '../api/cliente'

interface ContextoFavoritos {
  favoritos: string[]
  alternar: (simbolo: string) => void
  esFavorito: (simbolo: string) => boolean
}

// Clave vieja de localStorage: si quedó de una versión anterior, se migra a la base
const CLAVE_ALMACEN_VIEJA = 'mop.favoritos'

const Contexto = createContext<ContextoFavoritos | null>(null)

function favoritosLocalesViejos(): string[] {
  try {
    const crudo = localStorage.getItem(CLAVE_ALMACEN_VIEJA)
    return crudo ? (JSON.parse(crudo) as string[]) : []
  } catch {
    return []
  }
}

export function ProveedorFavoritos({ children }: { children: ReactNode }) {
  const [favoritos, setFavoritos] = useState<string[]>([])

  // Cargar de la base; migrar una sola vez lo que hubiera en localStorage
  useEffect(() => {
    let activo = true
    obtenerFavoritos()
      .then(async ({ tickers }) => {
        const viejos = favoritosLocalesViejos()
        const faltantes = viejos.filter((t) => !tickers.includes(t))
        if (faltantes.length > 0) {
          const { tickers: migrados } = await guardarFavoritos([...tickers, ...faltantes])
          localStorage.removeItem(CLAVE_ALMACEN_VIEJA)
          if (activo) setFavoritos(migrados)
          return
        }
        if (viejos.length > 0) localStorage.removeItem(CLAVE_ALMACEN_VIEJA)
        if (activo) setFavoritos(tickers)
      })
      .catch(() => {
        // Backend caído: mostrar lo local viejo antes que nada
        if (activo) setFavoritos(favoritosLocalesViejos())
      })
    return () => {
      activo = false
    }
  }, [])

  const alternar = useCallback((simbolo: string) => {
    setFavoritos((previos) => {
      const siguientes = previos.includes(simbolo)
        ? previos.filter((s) => s !== simbolo)
        : [...previos, simbolo]
      // Optimista: la UI cambia ya; si falla el guardado, el próximo load lo corrige
      guardarFavoritos(siguientes).catch(() => {})
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
