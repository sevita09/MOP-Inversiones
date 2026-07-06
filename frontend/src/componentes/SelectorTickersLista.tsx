import { useState } from 'react'
import { usarTickers } from '../hooks/usarTickers'
import { usarCategorias } from '../contextos/CategoriasContext'
import LogoTicker from './LogoTicker'
import type { Categoria, Paneles } from '../api/tipos'
import './SelectorTickersLista.css'

const GRUPOS: { clave: keyof Paneles; titulo: string }[] = [
  { clave: 'panel_lider', titulo: 'Panel Líder' },
  { clave: 'panel_general', titulo: 'Panel General' },
  { clave: 'cedears', titulo: 'CEDEARs' },
  { clave: 'indices', titulo: 'Índices' },
  { clave: 'cripto', titulo: 'Cripto' },
  { clave: 'dolar', titulo: 'Dólar' },
]

interface Props {
  categoria: Categoria
  alCerrar: () => void
}

/** Modal para armar una lista de un tirón: muestra todos los tickers de la app
 *  agrupados (los que ya están en la lista, arriba) y cada clic agrega o quita. */
function SelectorTickersLista({ categoria, alCerrar }: Props) {
  const paneles = usarTickers()
  const { categorias, alternarTicker } = usarCategorias()
  const [filtro, setFiltro] = useState('')

  // La categoría fresca del contexto (se actualiza con cada toggle)
  const actual = categorias.find((c) => c.id === categoria.id) ?? categoria

  const pasaFiltro = (simbolo: string) =>
    simbolo.toLowerCase().includes(filtro.trim().toLowerCase())

  const fila = (simbolo: string) => {
    const incluido = actual.tickers.includes(simbolo)
    return (
      <button
        key={simbolo}
        type="button"
        className={incluido ? 'fila-seleccionable incluido' : 'fila-seleccionable'}
        onClick={() => void alternarTicker(actual.id, simbolo)}
      >
        <LogoTicker ticker={simbolo} tamano={18} />
        <span className="simbolo-seleccionable">{simbolo}</span>
        <span className="tilde-seleccion">{incluido ? '✓' : '+'}</span>
      </button>
    )
  }

  return (
    <div className="fondo-selector-lista" onClick={alCerrar}>
      <div className="selector-lista" onClick={(evento) => evento.stopPropagation()}>
        <div className="cabecera-selector">
          <span>Armar “{actual.nombre}”</span>
          <button type="button" className="cerrar-selector" onClick={alCerrar}>×</button>
        </div>
        <input
          autoFocus
          className="filtro-selector"
          value={filtro}
          placeholder="Filtrar tickers…"
          onChange={(evento) => setFiltro(evento.target.value)}
        />
        <div className="cuerpo-selector">
          {actual.tickers.filter(pasaFiltro).length > 0 && (
            <section>
              <h3 className="titulo-grupo-selector">En la lista</h3>
              {actual.tickers.filter(pasaFiltro).map(fila)}
            </section>
          )}
          {paneles &&
            GRUPOS.map(({ clave, titulo }) => {
              const visibles = paneles[clave].filter(
                (s) => pasaFiltro(s) && !actual.tickers.includes(s),
              )
              if (visibles.length === 0) return null
              return (
                <section key={clave}>
                  <h3 className="titulo-grupo-selector">{titulo}</h3>
                  {visibles.map(fila)}
                </section>
              )
            })}
        </div>
      </div>
    </div>
  )
}

export default SelectorTickersLista
