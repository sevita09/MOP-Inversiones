import { useState } from 'react'
import { usarCategorias } from '../contextos/CategoriasContext'
import { usarTicker } from '../contextos/TickerContext'
import './MenuCategorias.css'

type Vista = 'menu' | 'nueva_lista'

/** Botón "+" junto al buscador. Abre un modal centrado para agregar el ticker
 *  activo a una lista de seguimiento o crear una lista nueva. */
function MenuCategorias() {
  const { categorias, crear, alternarTicker } = usarCategorias()
  const { ticker } = usarTicker()
  const [abierto, setAbierto] = useState(false)
  const [vista, setVista] = useState<Vista>('menu')
  const [nombre, setNombre] = useState('')
  const [mensaje, setMensaje] = useState('')

  const cerrar = () => {
    setAbierto(false)
    setVista('menu')
    setNombre('')
    setMensaje('')
  }

  const crearLista = async () => {
    const limpio = nombre.trim()
    if (!limpio) return
    try {
      await crear(limpio)
      setNombre('')
      setVista('menu')
      setMensaje('')
    } catch {
      setMensaje(`Ya existe una lista llamada ${limpio}`)
    }
  }

  return (
    <>
      <button
        type="button"
        className="boton-mas"
        title="Listas de seguimiento"
        onClick={() => setAbierto(true)}
      >
        +
      </button>
      {abierto && (
        <div className="fondo-modal-categorias" onClick={cerrar}>
          <div className="modal-categorias" onClick={(evento) => evento.stopPropagation()}>
            <div className="cabecera-modal">
              <span>Listas de seguimiento</span>
              <button type="button" className="cerrar-modal" onClick={cerrar}>×</button>
            </div>

            {vista === 'menu' && (
              <>
                <div className="titulo-seccion">Agregar {ticker} a una lista</div>
                {categorias.length === 0 && (
                  <div className="sin-categorias">Sin listas todavía</div>
                )}
                {categorias.map((categoria) => {
                  const incluido = categoria.tickers.includes(ticker)
                  return (
                    <button
                      key={categoria.id}
                      type="button"
                      className="opcion-categoria"
                      onClick={() => void alternarTicker(categoria.id, ticker)}
                    >
                      <span className="tilde">{incluido ? '✓' : ''}</span>
                      {categoria.nombre}
                      <span className="conteo">{categoria.tickers.length}</span>
                    </button>
                  )
                })}
                <div className="separador-modal" />
                <button
                  type="button"
                  className="opcion-categoria nueva"
                  onClick={() => { setVista('nueva_lista'); setMensaje('') }}
                >
                  <span className="tilde">＋</span>
                  Crear lista de seguimiento…
                </button>
              </>
            )}

            {vista === 'nueva_lista' && (
              <>
                <div className="titulo-seccion">Nueva lista de seguimiento</div>
                <div className="formulario-modal">
                  <input
                    autoFocus
                    value={nombre}
                    placeholder="Nombre (ej: Bancos)"
                    onChange={(evento) => setNombre(evento.target.value)}
                    onKeyDown={(evento) => {
                      if (evento.key === 'Enter') void crearLista()
                      if (evento.key === 'Escape') setVista('menu')
                    }}
                  />
                  <button type="button" onClick={() => void crearLista()}>Crear</button>
                  <button type="button" className="secundario" onClick={() => setVista('menu')}>
                    Volver
                  </button>
                </div>
              </>
            )}

            {mensaje && <div className="mensaje-modal">{mensaje}</div>}
          </div>
        </div>
      )}
    </>
  )
}

export default MenuCategorias
