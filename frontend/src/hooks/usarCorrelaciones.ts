import { useEffect, useState } from 'react'
import {
  obtenerCorrelacionPar,
  obtenerCorrelaciones,
  obtenerPapelesEnCartera,
} from '../api/cliente'
import type {
  CorrelacionPar,
  MatrizCorrelacion,
  Moneda,
  TemporalidadBot,
} from '../api/tipos'

/** Papeles con los que arranca la matriz: los de la cartera.
 *
 *  Es la pregunta que uno se hace primero —¿lo que tengo se mueve junto?—, y
 *  si todavía no hay cartera no adivina: devuelve vacío y la página propone. */
export function usarPapelesDeCartera(): string[] | null {
  const [papeles, setPapeles] = useState<string[] | null>(null)

  useEffect(() => {
    let vigente = true
    obtenerPapelesEnCartera()
      .then((cantidades) => vigente && setPapeles(Object.keys(cantidades).sort()))
      .catch(() => vigente && setPapeles([]))
    return () => {
      vigente = false
    }
  }, [])

  return papeles
}

export function usarMatrizCorrelacion(
  tickers: string[],
  temporalidad: TemporalidadBot,
  moneda: Moneda,
  desde?: number,
) {
  const [matriz, setMatriz] = useState<MatrizCorrelacion | null>(null)
  const [cargando, setCargando] = useState(false)
  const clave = tickers.join(',')

  useEffect(() => {
    if (tickers.length < 2) {
      setMatriz(null)
      return
    }
    let vigente = true
    setCargando(true)
    obtenerCorrelaciones(tickers, temporalidad, moneda, desde)
      .then((datos) => vigente && setMatriz(datos))
      .catch(() => vigente && setMatriz(null))
      .finally(() => vigente && setCargando(false))
    return () => {
      vigente = false
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [clave, temporalidad, moneda, desde])

  return { matriz, cargando }
}

export function usarCorrelacionPar(
  a: string | null,
  b: string | null,
  temporalidad: TemporalidadBot,
  moneda: Moneda,
  ventana: number,
  desde?: number,
) {
  const [par, setPar] = useState<CorrelacionPar | null>(null)

  useEffect(() => {
    if (!a || !b || a === b) {
      setPar(null)
      return
    }
    let vigente = true
    obtenerCorrelacionPar(a, b, temporalidad, moneda, ventana, desde)
      .then((datos) => vigente && setPar(datos))
      .catch(() => vigente && setPar(null))
    return () => {
      vigente = false
    }
  }, [a, b, temporalidad, moneda, ventana, desde])

  return par
}
