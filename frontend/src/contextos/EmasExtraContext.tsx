import {
  createContext,
  useCallback,
  useContext,
  useMemo,
  useState,
  type ReactNode,
} from 'react'
import type { Temporalidad } from '../api/tipos'
import type { TipoLinea } from './EstilosContext'

export type TipoMedia = 'exp' | 'simple'

// Una EMA/SMA extra que el usuario agrega sobre el precio, aparte de la central.
// El período y el tipo se guardan POR TEMPORALIDAD (cada una con su propio valor);
// el color y el estilo de línea (ancho/tipo) son únicos para la EMA.
export interface EmaExtra {
  id: string
  color: string
  ancho?: number
  tipoLinea?: TipoLinea
  periodo: Partial<Record<Temporalidad, number>>
  tipo: Partial<Record<Temporalidad, TipoMedia>>
}

export const ANCHO_EXTRA_DEFAULT = 2
export const TIPO_LINEA_EXTRA_DEFAULT: TipoLinea = 'solid'

export const PERIODO_EXTRA_DEFAULT = 50
export const TIPO_EXTRA_DEFAULT: TipoMedia = 'exp'

// Período/tipo efectivos de una EMA extra en una temporalidad (con sus defaults).
// Un período inválido (<1) cae al default para no romper el cálculo.
export function periodoExtraDe(ema: EmaExtra, temporalidad: Temporalidad): number {
  const p = ema.periodo[temporalidad]
  return p != null && p >= 1 ? p : PERIODO_EXTRA_DEFAULT
}
export function tipoExtraDe(ema: EmaExtra, temporalidad: Temporalidad): TipoMedia {
  return ema.tipo[temporalidad] ?? TIPO_EXTRA_DEFAULT
}

// Colores por default para las EMAs nuevas (rota por la paleta)
const COLORES_EXTRA = ['#39c5cf', '#db61a2', '#7ee787', '#f0883e', '#a371f7', '#ff7b72']

interface ContextoEmasExtra {
  emas: EmaExtra[]
  agregar: () => void
  quitar: (id: string) => void
  setColor: (id: string, color: string) => void
  setLinea: (id: string, cambios: { ancho?: number; tipoLinea?: TipoLinea }) => void
  setPeriodo: (id: string, temporalidad: Temporalidad, valor: number | undefined) => void
  setTipo: (id: string, temporalidad: Temporalidad, valor: TipoMedia) => void
}

const CLAVE = 'mop.emas_extra'
const Contexto = createContext<ContextoEmasExtra | null>(null)

function leer(): EmaExtra[] {
  try {
    const crudo = localStorage.getItem(CLAVE)
    return crudo ? (JSON.parse(crudo) as EmaExtra[]) : []
  } catch {
    return []
  }
}

export function ProveedorEmasExtra({ children }: { children: ReactNode }) {
  const [emas, setEmas] = useState<EmaExtra[]>(leer)

  const persistir = useCallback((siguiente: EmaExtra[]) => {
    localStorage.setItem(CLAVE, JSON.stringify(siguiente))
    setEmas(siguiente)
  }, [])

  const editar = useCallback(
    (id: string, cambio: (ema: EmaExtra) => EmaExtra) => {
      persistir(emas.map((e) => (e.id === id ? cambio(e) : e)))
    },
    [emas, persistir],
  )

  const agregar = useCallback(() => {
    const id = `ema-${Date.now()}`
    const color = COLORES_EXTRA[emas.length % COLORES_EXTRA.length]
    persistir([...emas, { id, color, periodo: {}, tipo: {} }])
  }, [emas, persistir])

  const quitar = useCallback(
    (id: string) => persistir(emas.filter((e) => e.id !== id)),
    [emas, persistir],
  )

  const setColor = useCallback(
    (id: string, color: string) => editar(id, (e) => ({ ...e, color })),
    [editar],
  )

  const setLinea = useCallback(
    (id: string, cambios: { ancho?: number; tipoLinea?: TipoLinea }) =>
      editar(id, (e) => ({ ...e, ...cambios })),
    [editar],
  )

  const setPeriodo = useCallback(
    (id: string, temporalidad: Temporalidad, valor: number | undefined) =>
      editar(id, (e) => {
        const periodo = { ...e.periodo }
        if (valor === undefined) delete periodo[temporalidad]
        else periodo[temporalidad] = valor
        return { ...e, periodo }
      }),
    [editar],
  )

  const setTipo = useCallback(
    (id: string, temporalidad: Temporalidad, valor: TipoMedia) =>
      editar(id, (e) => ({ ...e, tipo: { ...e.tipo, [temporalidad]: valor } })),
    [editar],
  )

  const valor = useMemo<ContextoEmasExtra>(
    () => ({ emas, agregar, quitar, setColor, setLinea, setPeriodo, setTipo }),
    [emas, agregar, quitar, setColor, setLinea, setPeriodo, setTipo],
  )

  return <Contexto.Provider value={valor}>{children}</Contexto.Provider>
}

export function usarEmasExtra(): ContextoEmasExtra {
  const contexto = useContext(Contexto)
  if (contexto === null) {
    throw new Error('usarEmasExtra debe usarse dentro de ProveedorEmasExtra')
  }
  return contexto
}
