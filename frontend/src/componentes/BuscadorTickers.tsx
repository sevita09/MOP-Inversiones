import { useEffect, useMemo, useState } from 'react'
import { usarTickers } from '../hooks/usarTickers'
import { usarTicker } from '../contextos/TickerContext'
import type { Paneles } from '../api/tipos'
import './BuscadorTickers.css'

function todosLosSimbolos(paneles: Paneles | null): string[] {
  if (!paneles) return []
  return [...paneles.panel_lider, ...paneles.panel_general, ...paneles.cedears, ...paneles.dolar]
}

function BuscadorTickers() {
  const paneles = usarTickers()
  const { elegirTicker } = usarTicker()
  const [abierto, setAbierto] = useState(false)
  const [texto, setTexto] = useState('')
  const [resaltado, setResaltado] = useState(0)

  // Cmd+K / Ctrl+K abre el buscador; Escape lo cierra
  useEffect(() => {
    const alTecla = (evento: KeyboardEvent) => {
      if ((evento.metaKey || evento.ctrlKey) && evento.key.toLowerCase() === 'k') {
        evento.preventDefault()
        setAbierto((previo) => !previo)
      } else if (evento.key === 'Escape') {
        setAbierto(false)
      }
    }
    window.addEventListener('keydown', alTecla)
    return () => window.removeEventListener('keydown', alTecla)
  }, [])

  const resultados = useMemo(() => {
    const simbolos = todosLosSimbolos(paneles)
    const consulta = texto.trim().toUpperCase()
    if (!consulta) return simbolos
    return simbolos.filter((simbolo) => simbolo.includes(consulta))
  }, [paneles, texto])

  // Reiniciar el resaltado cuando cambian los resultados
  useEffect(() => {
    setResaltado(0)
  }, [texto])

  if (!abierto) return null

  const cerrar = () => {
    setAbierto(false)
    setTexto('')
  }

  const elegir = (simbolo: string) => {
    elegirTicker(simbolo)
    cerrar()
  }

  const alTeclaEntrada = (evento: React.KeyboardEvent) => {
    if (evento.key === 'ArrowDown') {
      evento.preventDefault()
      setResaltado((i) => Math.min(i + 1, resultados.length - 1))
    } else if (evento.key === 'ArrowUp') {
      evento.preventDefault()
      setResaltado((i) => Math.max(i - 1, 0))
    } else if (evento.key === 'Enter' && resultados[resaltado]) {
      elegir(resultados[resaltado])
    }
  }

  return (
    <div className="buscador-fondo" onClick={cerrar}>
      <div className="buscador-modal" onClick={(e) => e.stopPropagation()}>
        <input
          className="buscador-input"
          type="text"
          placeholder="Buscar ticker…"
          value={texto}
          autoFocus
          onChange={(e) => setTexto(e.target.value)}
          onKeyDown={alTeclaEntrada}
        />
        <ul className="buscador-resultados">
          {resultados.map((simbolo, indice) => (
            <li key={simbolo}>
              <button
                type="button"
                className={`buscador-item${indice === resaltado ? ' resaltado' : ''}`}
                onClick={() => elegir(simbolo)}
                onMouseEnter={() => setResaltado(indice)}
              >
                {simbolo}
              </button>
            </li>
          ))}
          {resultados.length === 0 && <li className="buscador-vacio">Sin resultados</li>}
        </ul>
      </div>
    </div>
  )
}

export default BuscadorTickers
