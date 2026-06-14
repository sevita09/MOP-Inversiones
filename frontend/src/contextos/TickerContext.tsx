import {
  createContext,
  useCallback,
  useContext,
  useMemo,
  useState,
  type ReactNode,
} from 'react'

interface ContextoTicker {
  ticker: string
  elegirTicker: (ticker: string) => void
}

const CLAVE_ALMACEN = 'mop.ticker'
const TICKER_DEFAULT = 'GGAL'

const Contexto = createContext<ContextoTicker | null>(null)

function tickerInicial(): string {
  return localStorage.getItem(CLAVE_ALMACEN) ?? TICKER_DEFAULT
}

export function ProveedorTicker({ children }: { children: ReactNode }) {
  const [ticker, setTicker] = useState<string>(tickerInicial)

  const elegirTicker = useCallback((nuevo: string) => {
    localStorage.setItem(CLAVE_ALMACEN, nuevo)
    setTicker(nuevo)
  }, [])

  const valor = useMemo<ContextoTicker>(
    () => ({ ticker, elegirTicker }),
    [ticker, elegirTicker],
  )

  return <Contexto.Provider value={valor}>{children}</Contexto.Provider>
}

export function usarTicker(): ContextoTicker {
  const contexto = useContext(Contexto)
  if (contexto === null) {
    throw new Error('usarTicker debe usarse dentro de ProveedorTicker')
  }
  return contexto
}
