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
  opacidad?: number // 0..1 (histogramas y líneas que lo soporten, p.ej. VPVR)
}

// Overrides del usuario por elemento (id → estilo). El recomendado vive en el
// código; acá solo se guarda lo que el usuario cambió, y pisa al recomendado.
type Overrides = Record<string, Estilo>

// Parámetros del usuario por indicador (nombre backend → {clave: valor}). Casi
// todos son numéricos; el tipo de media (exp/simple) es string. Mismo principio:
// solo se guarda lo que el usuario cambió; el resto usa el default.
export type ValorParam = number | string
export type Params = Record<string, ValorParam>
type ParamsPorIndicador = Record<string, Params>

interface ContextoEstilos {
  // Estilo efectivo = recomendado con los campos que el usuario haya cambiado
  estiloDe: (id: string, recomendado: Estilo) => Estilo
  // Lo que el usuario tiene guardado para ese id (para saber qué está override)
  overrideDe: (id: string) => Estilo
  guardar: (id: string, cambios: Estilo) => void
  volver: (id: string) => void
  // Parámetros numéricos overrideados del usuario para un indicador
  paramsDe: (indicador: string) => Params
  guardarParam: (indicador: string, clave: string, valor: ValorParam) => void
  borrarParam: (indicador: string, clave: string) => void
}

const CLAVE = 'mop.estilos'
const CLAVE_PARAMS = 'mop.params'
const Contexto = createContext<ContextoEstilos | null>(null)

function leer(): Overrides {
  try {
    const crudo = localStorage.getItem(CLAVE)
    return crudo ? (JSON.parse(crudo) as Overrides) : {}
  } catch {
    return {}
  }
}

function leerParams(): ParamsPorIndicador {
  try {
    const crudo = localStorage.getItem(CLAVE_PARAMS)
    return crudo ? (JSON.parse(crudo) as ParamsPorIndicador) : {}
  } catch {
    return {}
  }
}

export function ProveedorEstilos({ children }: { children: ReactNode }) {
  const [overrides, setOverrides] = useState<Overrides>(leer)
  const [params, setParams] = useState<ParamsPorIndicador>(leerParams)

  // Updates funcionales: varios cambios en el mismo render (p.ej. "Volver" sobre
  // un grupo de 3 elementos) no se pisan entre sí partiendo de un estado viejo.
  const guardar = useCallback((id: string, cambios: Estilo) => {
    setOverrides((prev) => {
      const siguiente = { ...prev, [id]: { ...prev[id], ...cambios } }
      try {
        localStorage.setItem(CLAVE, JSON.stringify(siguiente))
      } catch {
        /* almacenamiento no disponible: igual queda en memoria */
      }
      return siguiente
    })
  }, [])

  const volver = useCallback((id: string) => {
    setOverrides((prev) => {
      const siguiente = { ...prev }
      delete siguiente[id]
      try {
        localStorage.setItem(CLAVE, JSON.stringify(siguiente))
      } catch {
        /* almacenamiento no disponible */
      }
      return siguiente
    })
  }, [])

  const estiloDe = useCallback(
    (id: string, recomendado: Estilo): Estilo => ({ ...recomendado, ...overrides[id] }),
    [overrides],
  )

  const overrideDe = useCallback((id: string): Estilo => overrides[id] ?? {}, [overrides])

  const paramsDe = useCallback(
    (indicador: string): Params => params[indicador] ?? {},
    [params],
  )

  const guardarParam = useCallback((indicador: string, clave: string, valor: ValorParam) => {
    setParams((prev) => {
      const siguiente = { ...prev, [indicador]: { ...prev[indicador], [clave]: valor } }
      try {
        localStorage.setItem(CLAVE_PARAMS, JSON.stringify(siguiente))
      } catch {
        /* almacenamiento no disponible */
      }
      return siguiente
    })
  }, [])

  const borrarParam = useCallback((indicador: string, clave: string) => {
    setParams((prev) => {
      const delIndicador = { ...prev[indicador] }
      delete delIndicador[clave]
      const siguiente = { ...prev }
      if (Object.keys(delIndicador).length > 0) siguiente[indicador] = delIndicador
      else delete siguiente[indicador]
      try {
        localStorage.setItem(CLAVE_PARAMS, JSON.stringify(siguiente))
      } catch {
        /* almacenamiento no disponible */
      }
      return siguiente
    })
  }, [])

  const valor = useMemo<ContextoEstilos>(
    () => ({
      estiloDe,
      overrideDe,
      guardar,
      volver,
      paramsDe,
      guardarParam,
      borrarParam,
    }),
    [estiloDe, overrideDe, guardar, volver, paramsDe, guardarParam, borrarParam],
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
