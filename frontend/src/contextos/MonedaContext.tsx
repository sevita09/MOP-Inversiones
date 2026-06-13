import {
  createContext,
  useCallback,
  useContext,
  useMemo,
  useState,
  type ReactNode,
} from 'react'

export type Moneda = 'ARS' | 'USD'

interface ContextoMoneda {
  moneda: Moneda
  alternarMoneda: () => void
  esUSD: boolean
}

const CLAVE_ALMACEN = 'mop.moneda'

const Contexto = createContext<ContextoMoneda | null>(null)

function monedaInicial(): Moneda {
  return localStorage.getItem(CLAVE_ALMACEN) === 'USD' ? 'USD' : 'ARS'
}

export function ProveedorMoneda({ children }: { children: ReactNode }) {
  const [moneda, setMoneda] = useState<Moneda>(monedaInicial)

  const alternarMoneda = useCallback(() => {
    setMoneda((actual) => {
      const siguiente: Moneda = actual === 'ARS' ? 'USD' : 'ARS'
      localStorage.setItem(CLAVE_ALMACEN, siguiente)
      return siguiente
    })
  }, [])

  const valor = useMemo<ContextoMoneda>(
    () => ({ moneda, alternarMoneda, esUSD: moneda === 'USD' }),
    [moneda, alternarMoneda],
  )

  return <Contexto.Provider value={valor}>{children}</Contexto.Provider>
}

export function usarMoneda(): ContextoMoneda {
  const contexto = useContext(Contexto)
  if (contexto === null) {
    throw new Error('usarMoneda debe usarse dentro de ProveedorMoneda')
  }
  return contexto
}
