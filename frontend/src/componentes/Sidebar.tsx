import { usarTickers } from '../hooks/usarTickers'
import { usarPrecios } from '../hooks/usarPrecios'
import { usarFavoritos } from '../hooks/usarFavoritos'
import { usarTicker } from '../contextos/TickerContext'
import FilaTicker from './FilaTicker'
import type { Paneles } from '../api/tipos'
import './Sidebar.css'

const GRUPOS: { clave: keyof Paneles; titulo: string }[] = [
  { clave: 'panel_lider', titulo: 'Panel Líder' },
  { clave: 'panel_general', titulo: 'Panel General' },
  { clave: 'cedears', titulo: 'CEDEARs' },
  { clave: 'dolar', titulo: 'Dólar' },
]

function abrirBuscador() {
  window.dispatchEvent(new KeyboardEvent('keydown', { key: 'k', metaKey: true }))
}

function Sidebar() {
  const paneles = usarTickers()
  const precios = usarPrecios()
  const { favoritos, alternar, esFavorito } = usarFavoritos()
  const { ticker: activo, elegirTicker } = usarTicker()

  const fila = (simbolo: string) => (
    <FilaTicker
      key={simbolo}
      simbolo={simbolo}
      precio={precios[simbolo]}
      activo={simbolo === activo}
      favorito={esFavorito(simbolo)}
      alElegir={elegirTicker}
      alAlternarFavorito={alternar}
    />
  )

  return (
    <aside className="sidebar">
      <button type="button" className="boton-buscar" onClick={abrirBuscador}>
        <span>Buscar</span>
        <kbd>⌘K</kbd>
      </button>
      {favoritos.length > 0 && (
        <section className="grupo-tickers">
          <h2 className="grupo-titulo">Favoritos</h2>
          {favoritos.map(fila)}
        </section>
      )}
      {paneles &&
        GRUPOS.map(({ clave, titulo }) => (
          <section key={clave} className="grupo-tickers">
            <h2 className="grupo-titulo">{titulo}</h2>
            {paneles[clave].map(fila)}
          </section>
        ))}
    </aside>
  )
}

export default Sidebar
