import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from 'react'
import {
  agregarTickerACategoria,
  crearCategoria,
  eliminarCategoria,
  obtenerCategorias,
  quitarTickerDeCategoria,
} from '../api/cliente'
import type { Categoria } from '../api/tipos'

interface ContextoCategorias {
  categorias: Categoria[]
  crear: (nombre: string) => Promise<void>
  eliminar: (id: number) => Promise<void>
  alternarTicker: (id: number, ticker: string) => Promise<void>
}

const Contexto = createContext<ContextoCategorias | null>(null)

export function ProveedorCategorias({ children }: { children: ReactNode }) {
  const [categorias, setCategorias] = useState<Categoria[]>([])

  const recargar = useCallback(
    () =>
      obtenerCategorias()
        .then(setCategorias)
        .catch(() => {
          // Backend caído: se reintenta en la próxima acción
        }),
    [],
  )

  useEffect(() => {
    void recargar()
  }, [recargar])

  const crear = useCallback(
    async (nombre: string) => {
      await crearCategoria(nombre)
      await recargar()
    },
    [recargar],
  )

  const eliminar = useCallback(
    async (id: number) => {
      await eliminarCategoria(id)
      await recargar()
    },
    [recargar],
  )

  const alternarTicker = useCallback(
    async (id: number, ticker: string) => {
      const categoria = categorias.find((c) => c.id === id)
      if (categoria?.tickers.includes(ticker)) {
        await quitarTickerDeCategoria(id, ticker)
      } else {
        await agregarTickerACategoria(id, ticker)
      }
      await recargar()
    },
    [categorias, recargar],
  )

  const valor = useMemo<ContextoCategorias>(
    () => ({ categorias, crear, eliminar, alternarTicker }),
    [categorias, crear, eliminar, alternarTicker],
  )

  return <Contexto.Provider value={valor}>{children}</Contexto.Provider>
}

export function usarCategorias(): ContextoCategorias {
  const contexto = useContext(Contexto)
  if (contexto === null) {
    throw new Error('usarCategorias debe usarse dentro de ProveedorCategorias')
  }
  return contexto
}
