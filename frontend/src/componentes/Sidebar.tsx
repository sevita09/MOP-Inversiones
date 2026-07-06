import { usarTickers } from '../hooks/usarTickers'
import { usarPrecios } from '../hooks/usarPrecios'
import { usarEstadoPersistente } from '../hooks/usarEstadoPersistente'
import { usarFavoritos } from '../contextos/FavoritosContext'
import { usarCategorias } from '../contextos/CategoriasContext'
import { usarTicker } from '../contextos/TickerContext'
import { useState } from 'react'
import FilaTicker from './FilaTicker'
import MenuCategorias from './MenuCategorias'
import SelectorTickersLista from './SelectorTickersLista'
import type { Categoria, Paneles } from '../api/tipos'
import './Sidebar.css'

const GRUPOS: { clave: keyof Paneles; titulo: string }[] = [
  { clave: 'panel_lider', titulo: 'Panel Líder' },
  { clave: 'panel_general', titulo: 'Panel General' },
  { clave: 'cedears', titulo: 'CEDEARs' },
  { clave: 'indices', titulo: 'Índices' },
  { clave: 'cripto', titulo: 'Cripto' },
  { clave: 'dolar', titulo: 'Dólar' },
]

type Pestana = 'tickers' | 'listas'

function abrirBuscador() {
  window.dispatchEvent(new KeyboardEvent('keydown', { key: 'k', metaKey: true }))
}

function Sidebar() {
  const paneles = usarTickers()
  const precios = usarPrecios()
  const { favoritos, alternar, esFavorito } = usarFavoritos()
  const { categorias, eliminar } = usarCategorias()
  const { ticker: activo, elegirTicker } = usarTicker()
  const [pestana, setPestana] = usarEstadoPersistente<Pestana>('mop.sidebar.pestana', 'tickers')
  const [listaAbierta, setListaAbierta] = useState<Categoria | null>(null)

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
      <div className="barra-sidebar">
        <button type="button" className="boton-buscar" onClick={abrirBuscador}>
          <span>Buscar</span>
          <kbd>⌘K</kbd>
        </button>
        <MenuCategorias />
      </div>

      <div className="pestanas-sidebar">
        <button
          type="button"
          className={pestana === 'tickers' ? 'pestana activa' : 'pestana'}
          onClick={() => setPestana('tickers')}
        >
          Tickers
        </button>
        <button
          type="button"
          className={pestana === 'listas' ? 'pestana activa' : 'pestana'}
          onClick={() => setPestana('listas')}
        >
          Listas
        </button>
      </div>

      <div className="cuerpo-sidebar">
        {pestana === 'tickers' && (
          <>
            {favoritos.length > 0 && (
              <section className="grupo-tickers">
                <h2 className="grupo-titulo">Favoritos</h2>
                {favoritos.map(fila)}
              </section>
            )}
            {paneles &&
              GRUPOS.map(({ clave, titulo }) =>
                paneles[clave].length > 0 ? (
                  <section key={clave} className="grupo-tickers">
                    <h2 className="grupo-titulo">{titulo}</h2>
                    {paneles[clave].map(fila)}
                  </section>
                ) : null,
              )}
          </>
        )}

        {pestana === 'listas' && (
          <>
            {categorias.length === 0 && (
              <p className="categoria-vacia">
                Creá tu primera lista de seguimiento con el botón +
              </p>
            )}
            {categorias.map((categoria) => (
              <section key={categoria.id} className="grupo-tickers">
                <h2 className="grupo-titulo con-borrar">
                  {categoria.nombre}
                  <span className="acciones-lista">
                    <button
                      type="button"
                      className="armar-lista"
                      title={`Agregar o quitar tickers de ${categoria.nombre}`}
                      onClick={() => setListaAbierta(categoria)}
                    >
                      +
                    </button>
                    <button
                      type="button"
                      className="borrar-categoria"
                      title={`Borrar la lista ${categoria.nombre}`}
                      onClick={() => void eliminar(categoria.id)}
                    >
                      ×
                    </button>
                  </span>
                </h2>
                {categoria.tickers.length > 0 ? (
                  categoria.tickers.map(fila)
                ) : (
                  <p className="categoria-vacia">Sumá tickers con el botón +</p>
                )}
              </section>
            ))}
          </>
        )}
      </div>
      {listaAbierta && (
        <SelectorTickersLista
          categoria={listaAbierta}
          alCerrar={() => setListaAbierta(null)}
        />
      )}
    </aside>
  )
}

export default Sidebar
