import {
  createContext,
  useCallback,
  useContext,
  useMemo,
  useState,
  type ReactNode,
} from 'react'

export type TipoLinea = 'solid' | 'dashed' | 'dotted'

export interface Estilo {
  color?: string
  ancho?: number
  tipoLinea?: TipoLinea
}

// Overrides del usuario por elemento (id → estilo). El recomendado vive en el
// código; acá solo se guarda lo que el usuario cambió, y pisa al recomendado.
type Overrides = Record<string, Estilo>

interface ContextoEstilos {
  // Estilo efectivo = recomendado con los campos que el usuario haya cambiado
  estiloDe: (id: string, recomendado: Estilo) => Estilo
  // Lo que el usuario tiene guardado para ese id (para saber qué está override)
  overrideDe: (id: string) => Estilo
  guardar: (id: string, cambios: Estilo) => void
  volver: (id: string) => void
}

const CLAVE = 'mop.estilos'
const Contexto = createContext<ContextoEstilos | null>(null)

function leer(): Overrides {
  try {
    const crudo = localStorage.getItem(CLAVE)
    return crudo ? (JSON.parse(crudo) as Overrides) : {}
  } catch {
    return {}
  }
}

export function ProveedorEstilos({ children }: { children: ReactNode }) {
  const [overrides, setOverrides] = useState<Overrides>(leer)

  const persistir = useCallback((siguiente: Overrides) => {
    localStorage.setItem(CLAVE, JSON.stringify(siguiente))
    setOverrides(siguiente)
  }, [])

  const guardar = useCallback(
    (id: string, cambios: Estilo) => {
      persistir({ ...overrides, [id]: { ...overrides[id], ...cambios } })
    },
    [overrides, persistir],
  )

  const volver = useCallback(
    (id: string) => {
      const siguiente = { ...overrides }
      delete siguiente[id]
      persistir(siguiente)
    },
    [overrides, persistir],
  )

  const estiloDe = useCallback(
    (id: string, recomendado: Estilo): Estilo => ({ ...recomendado, ...overrides[id] }),
    [overrides],
  )

  const overrideDe = useCallback((id: string): Estilo => overrides[id] ?? {}, [overrides])

  const valor = useMemo<ContextoEstilos>(
    () => ({ estiloDe, overrideDe, guardar, volver }),
    [estiloDe, overrideDe, guardar, volver],
  )

  return <Contexto.Provider value={valor}>{children}</Contexto.Provider>
}

export function usarEstilos(): ContextoEstilos {
  const contexto = useContext(Contexto)
  if (contexto === null) {
    throw new Error('usarEstilos debe usarse dentro de ProveedorEstilos')
  }
  return contexto
}

// Mapea el tipo de línea propio al LineStyle de lightweight-charts (0/1/2)
export function aLineStyle(tipo: TipoLinea | undefined): number {
  if (tipo === 'dotted') return 1
  if (tipo === 'dashed') return 2
  return 0
}

// Aplica una opacidad a un color hex (#rrggbb) devolviendo rgba(). Si ya viene
// como rgba/otro formato, lo devuelve tal cual.
export function conOpacidad(color: string, opacidad: number): string {
  const m = /^#([0-9a-f]{6})$/i.exec(color)
  if (!m) return color
  const n = parseInt(m[1], 16)
  const r = (n >> 16) & 255
  const g = (n >> 8) & 255
  const b = n & 255
  return `rgba(${r}, ${g}, ${b}, ${opacidad})`
}
