import { useEffect, useRef } from 'react'
import { usarTickers } from './usarTickers'
import { usarTicker } from '../contextos/TickerContext'
import { usarMoneda } from '../contextos/MonedaContext'
import { usarFavoritos } from '../contextos/FavoritosContext'
import type { Paneles, Temporalidad } from '../api/tipos'

const POR_TECLA: Record<string, Temporalidad> = {
  '1': 'H',
  '2': 'D',
  '3': 'S',
  '4': 'M',
}

// Mismo orden que el sidebar: favoritos arriba (con sus duplicados en los
// paneles) — la navegación trackea la POSICIÓN, no el valor, así un favorito
// que también está en su panel se recorre en ambas listas sin generar loop.
function listaNavegable(paneles: Paneles | null, favoritos: string[]): string[] {
  if (!paneles) return []
  return [
    ...favoritos,
    ...paneles.panel_lider,
    ...paneles.panel_general,
    ...paneles.cedears,
    ...paneles.dolar,
  ]
}

function editando(objetivo: EventTarget | null): boolean {
  const el = objetivo as HTMLElement | null
  return !!el && (el.tagName === 'INPUT' || el.tagName === 'TEXTAREA' || el.isContentEditable)
}

export function usarAtajosTeclado(alTemporalidad: (t: Temporalidad) => void) {
  const paneles = usarTickers()
  const { ticker, elegirTicker } = usarTicker()
  const { alternarMoneda } = usarMoneda()
  const { favoritos } = usarFavoritos()
  // Posición actual en la lista navegable (no el valor): permite duplicados
  // —un favorito que también está en su panel— sin que las flechas hagan loop.
  const indiceNav = useRef(-1)

  useEffect(() => {
    const alTecla = (e: KeyboardEvent) => {
      // No interferir con atajos del navegador, el buscador (Cmd+K) ni el tipeo
      if (e.metaKey || e.ctrlKey || e.altKey || editando(e.target)) return

      if (e.key === 'ArrowUp' || e.key === 'ArrowDown') {
        const lista = listaNavegable(paneles, favoritos)
        if (lista.length === 0) return
        // Si el índice quedó desincronizado (cambió el ticker por click/buscador),
        // reubicar en la primera aparición del ticker activo
        let actual = indiceNav.current
        if (actual < 0 || actual >= lista.length || lista[actual] !== ticker) {
          actual = lista.indexOf(ticker)
        }
        if (actual === -1) return
        e.preventDefault()
        const siguiente = e.key === 'ArrowDown'
          ? Math.min(actual + 1, lista.length - 1)
          : Math.max(actual - 1, 0)
        indiceNav.current = siguiente
        elegirTicker(lista[siguiente])
      } else if (POR_TECLA[e.key]) {
        e.preventDefault()
        alTemporalidad(POR_TECLA[e.key])
      } else if (e.key === '$') {
        e.preventDefault()
        alternarMoneda()
      }
    }
    window.addEventListener('keydown', alTecla)
    return () => window.removeEventListener('keydown', alTecla)
  }, [paneles, favoritos, ticker, elegirTicker, alternarMoneda, alTemporalidad])
}
