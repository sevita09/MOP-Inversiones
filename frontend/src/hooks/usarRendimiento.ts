import { useEffect, useState } from 'react'
import { obtenerRealizado, obtenerRendimiento } from '../api/cliente'
import type { Moneda, Realizado, Rendimiento } from '../api/tipos'

/** Meses hacia atrás de cada período; `null` es toda la historia. */
export const PERIODOS: { clave: string; meses: number | null }[] = [
  { clave: '1M', meses: 1 },
  { clave: '3M', meses: 3 },
  { clave: '6M', meses: 6 },
  { clave: '1A', meses: 12 },
  { clave: '5A', meses: 60 },
  { clave: 'Todo', meses: null },
]

function fechaDesde(meses: number | null): string | undefined {
  if (meses === null) return undefined
  const fecha = new Date()
  fecha.setMonth(fecha.getMonth() - meses)
  return fecha.toISOString().slice(0, 10)
}

/** Curva de rendimiento contra los benchmarks y P&L realizado, en la moneda pedida.
 *
 * La moneda es propia de esta vista, no la global del gráfico: acá se mira la
 * cartera medida en pesos o en dólares, que son dos preguntas distintas. */
export function usarRendimiento(periodo: string, moneda: Moneda) {
  const [rendimiento, setRendimiento] = useState<Rendimiento | null>(null)
  const [realizado, setRealizado] = useState<Realizado | null>(null)
  const [cargando, setCargando] = useState(true)

  useEffect(() => {
    let vigente = true
    const meses = PERIODOS.find((p) => p.clave === periodo)?.meses ?? null
    setCargando(true)
    void Promise.all([obtenerRendimiento(moneda, fechaDesde(meses)), obtenerRealizado()])
      .then(([curva, cerradas]) => {
        if (!vigente) return
        setRendimiento(curva)
        setRealizado(cerradas)
      })
      .catch(() => {
        if (!vigente) return
        setRendimiento(null)
        setRealizado(null)
      })
      .finally(() => {
        if (vigente) setCargando(false)
      })
    return () => {
      vigente = false
    }
  }, [moneda, periodo])

  return { rendimiento, realizado, cargando }
}
