import { usarTickers } from '../hooks/usarTickers'
import { usarTicker } from '../contextos/TickerContext'
import type { Paneles } from '../api/tipos'
import './Sidebar.css'

const GRUPOS: { clave: keyof Paneles; titulo: string }[] = [
  { clave: 'panel_lider', titulo: 'Panel Líder' },
  { clave: 'panel_general', titulo: 'Panel General' },
  { clave: 'cedears', titulo: 'CEDEARs' },
  { clave: 'dolar', titulo: 'Dólar' },
]

function Sidebar() {
  const paneles = usarTickers()
  const { ticker: activo, elegirTicker } = usarTicker()

  return (
    <aside className="sidebar">
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
                {simbolo}
              </button>
            ))}
          </section>
        ))}
    </aside>
  )
}

export default Sidebar
