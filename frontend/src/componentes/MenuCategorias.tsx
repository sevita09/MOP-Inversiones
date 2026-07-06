import { useState } from 'react'
import { agregarTickerNuevo } from '../api/cliente'
import { usarCategorias } from '../contextos/CategoriasContext'
import { usarTicker } from '../contextos/TickerContext'
import { EVENTO_TICKERS } from '../hooks/usarTickers'
import './MenuCategorias.css'

type Vista = 'menu' | 'nueva_lista' | 'nuevo_ticker'

const GRUPOS_ALTA = [
  { clave: 'panel_lider', titulo: 'Panel Líder' },
  { clave: 'panel_general', titulo: 'Panel General' },
  { clave: 'cedears', titulo: 'CEDEARs' },
  { clave: 'indices', titulo: 'Índices' },
  { clave: 'cripto', titulo: 'Cripto' },
  { clave: 'dolar', titulo: 'Dólar' },
]

/** Botón "+" junto al buscador. Abre un modal centrado para: agregar el ticker
 *  activo a una lista de seguimiento, crear una lista nueva, o dar de alta un
 *  ticker que no está en la app (baja su historia de Yahoo). */
function MenuCategorias() {
  const { categorias, crear, alternarTicker } = usarCategorias()
  const { ticker } = usarTicker()
  const [abierto, setAbierto] = useState(false)
  const [vista, setVista] = useState<Vista>('menu')
  const [nombre, setNombre] = useState('')
  const [simbolo, setSimbolo] = useState('')
  const [grupo, setGrupo] = useState('cedears')
  const [mensaje, setMensaje] = useState('')
  const [descargando, setDescargando] = useState(false)

  const cerrar = () => {
    setAbierto(false)
    setVista('menu')
    setNombre('')
    setSimbolo('')
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

  const altaTicker = async () => {
    const limpio = simbolo.trim().toUpperCase()
    if (!limpio) return
    setDescargando(true)
    setMensaje('')
    try {
      await agregarTickerNuevo(limpio, grupo)
      window.dispatchEvent(new Event(EVENTO_TICKERS))
      setSimbolo('')
      setVista('menu')
      setMensaje(`${limpio} agregado — descargando su historia…`)
    } catch {
      setMensaje(`No se encontró ${limpio} en Yahoo Finance`)
    } finally {
      setDescargando(false)
    }
  }

  return (
    <>
      <button
        type="button"
        className="boton-mas"
        title="Listas de seguimiento y tickers"
        onClick={() => setAbierto(true)}
      >
        +
      </button>
      {abierto && (
        <div className="fondo-modal-categorias" onClick={cerrar}>
          <div className="modal-categorias" onClick={(evento) => evento.stopPropagation()}>
            <div className="cabecera-modal">
              <span>Listas y tickers</span>
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
                <button
                  type="button"
                  className="opcion-categoria nueva"
                  onClick={() => { setVista('nuevo_ticker'); setMensaje('') }}
                >
                  <span className="tilde">＋</span>
                  Agregar ticker nuevo…
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

            {vista === 'nuevo_ticker' && (
              <>
                <div className="titulo-seccion">Agregar ticker nuevo</div>
                <p className="ayuda-modal">
                  Se valida contra Yahoo Finance y se descargan su historia y su
                  logo. Ej: MSFT (CEDEAR), MERV (índice), BTC (cripto).
                </p>
                <div className="titulo-seccion">¿A qué grupo va?</div>
                <div className="grupos-alta">
                  {GRUPOS_ALTA.map(({ clave, titulo }) => (
                    <button
                      key={clave}
                      type="button"
                      className={clave === grupo ? 'chip-grupo activo' : 'chip-grupo'}
                      onClick={() => setGrupo(clave)}
                    >
                      {titulo}
                    </button>
                  ))}
                </div>
                <div className="formulario-modal">
                  <input
                    autoFocus
                    value={simbolo}
                    placeholder="Símbolo (ej: MSFT)"
                    onChange={(evento) => setSimbolo(evento.target.value.toUpperCase())}
                    onKeyDown={(evento) => {
                      if (evento.key === 'Enter') void altaTicker()
                      if (evento.key === 'Escape') setVista('menu')
                    }}
                  />
                  <button type="button" disabled={descargando} onClick={() => void altaTicker()}>
                    {descargando ? 'Validando…' : 'Agregar'}
                  </button>
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
