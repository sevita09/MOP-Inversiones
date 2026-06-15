import { useCallback, useState } from 'react'

// Como useState pero guarda el valor en localStorage bajo `clave`.
export function usarEstadoPersistente<T>(
  clave: string,
  inicial: T,
): [T, (valor: T) => void] {
  const [valor, setValor] = useState<T>(() => {
    try {
      const crudo = localStorage.getItem(clave)
      return crudo !== null ? (JSON.parse(crudo) as T) : inicial
    } catch {
      return inicial
    }
  })

  const guardar = useCallback(
    (nuevo: T) => {
      setValor(nuevo)
      try {
        localStorage.setItem(clave, JSON.stringify(nuevo))
      } catch {
        /* almacenamiento no disponible: igual queda en memoria */
      }
    },
    [clave],
  )

  return [valor, guardar]
}
