import { usarTickers } from '../hooks/usarTickers'
import { usarPrecios } from '../hooks/usarPrecios'
import { usarTicker } from '../contextos/TickerContext'
import type { Paneles, Precio } from '../api/tipos'
import './Sidebar.css'

const GRUPOS: { clave: keyof Paneles; titulo: string }[] = [
  { clave: 'panel_lider', titulo: 'Panel Líder' },
  { clave: 'panel_general', titulo: 'Panel General' },
  { clave: 'cedears', titulo: 'CEDEARs' },
  { clave: 'dolar', titulo: 'Dólar' },
]

function formatearVariacion(pct: number): string {
  return `${pct >= 0 ? '+' : ''}${pct.toFixed(2)}%`
}

function Variacion({ precio }: { precio: Precio | undefined }) {
  if (!precio || precio.variacion_pct === null) return null
  const positivo = precio.variacion_pct >= 0
  return (
    <span className={`ticker-variacion ${positivo ? 'var-verde' : 'var-roja'}`}>
      {formatearVariacion(precio.variacion_pct)}
    </span>
  )
}

function Sidebar() {
  const paneles = usarTickers()
  const precios = usarPrecios()
  const { ticker: activo, elegirTicker } = usarTicker()

  const abrirBuscador = () => {
    window.dispatchEvent(
      new KeyboardEvent('keydown', { key: 'k', metaKey: true }),
    )
  }

  return (
    <aside className="sidebar">
      <button type="button" className="boton-buscar" onClick={abrirBuscador}>
        <span>Buscar</span>
        <kbd>⌘K</kbd>
      </button>
      {paneles &&
        GRUPOS.map(({ clave, titulo }) => (
          <section key={clave} className="grupo-tickers">
            <h2 className="grupo-titulo">{titulo}</h2>
            {paneles[clave].map((simbolo) => (
              <button
                key={simbolo}
                type="button"
                className={`fila-ticker${simbolo === activo ? ' activo' : ''}`}
                onClick={() => elegirTicker(simbolo)}
              >
                <span className="ticker-simbolo">{simbolo}</span>
                <Variacion precio={precios[simbolo]} />
              </button>
            ))}
          </section>
        ))}
    </aside>
  )
}

export default Sidebar
