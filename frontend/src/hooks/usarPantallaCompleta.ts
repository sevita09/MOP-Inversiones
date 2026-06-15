import { useCallback, useEffect, useState, type RefObject } from 'react'

export function usarPantallaCompleta(ref: RefObject<HTMLElement>) {
  const [activa, setActiva] = useState(false)

  useEffect(() => {
    const alCambiar = () => setActiva(document.fullscreenElement === ref.current)
    document.addEventListener('fullscreenchange', alCambiar)
    return () => document.removeEventListener('fullscreenchange', alCambiar)
  }, [ref])

  const alternar = useCallback(() => {
    if (document.fullscreenElement) {
      document.exitFullscreen()
    } else {
      ref.current?.requestFullscreen()
    }
  }, [ref])

  return { activa, alternar }
}
