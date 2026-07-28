import { useEffect, useMemo, useState } from 'react'
import { crearSplit, eliminarSplit, obtenerSplits } from '../../api/cliente'
import type { Split } from '../../api/tipos'
import InputNumero from '../bots/InputNumero'
import LogoTicker from '../LogoTicker'
import { usarTickers } from '../../hooks/usarTickers'
import './PanelSplits.css'

interface Props {
  alCerrar: () => void
  alCambiar: () => void // para refrescar las tenencias
}

const HOY = () => new Date().toISOString().slice(0, 10)

function fecha(texto: string): string {
  const [anio, mes, dia] = texto.split('-')
  return `${dia}/${mes}/${anio.slice(2)}`
}

/** Cómo se lee el ratio: 3 → "3:1", 0.1 → "1:10". */
function describirRatio(ratio: number): string {
  if (ratio >= 1) return `${ratio}:1 — cada papel pasa a ser ${ratio}`
  const inverso = Math.round(1 / ratio)
  return `1:${inverso} — cada ${inverso} papeles pasan a ser 1`
}

/** Alta y baja de splits. No mueven plata: ajustan la cantidad de papeles y su
 *  precio, dejando el costo total igual. */
function PanelSplits({ alCerrar, alCambiar }: Props) {
  const paneles = usarTickers()
  const [splits, setSplits] = useState<Split[]>([])
  const [ticker, setTicker] = useState('')
  const [busqueda, setBusqueda] = useState('')
  const [fechaSplit, setFechaSplit] = useState(HOY())
  const [ratio, setRatio] = useState<number | null>(null)
  const [nota, setNota] = useState('')
  const [mensaje, setMensaje] = useState('')
  const [guardando, setGuardando] = useState(false)

  const cargar = () => {
    obtenerSplits()
      .then(setSplits)
      .catch(() => setSplits([]))
  }

  useEffect(cargar, [])

  const candidatos = useMemo(() => {
    if (!paneles) return []
    const todos = [
      ...paneles.panel_lider,
      ...paneles.panel_general,
      ...paneles.cedears,
      ...paneles.indices,
      ...paneles.cripto,
    ]
    const consulta = busqueda.trim().toUpperCase()
    if (!consulta) return []
    return todos.filter((simbolo) => simbolo.includes(consulta)).slice(0, 6)
  }, [paneles, busqueda])

  const guardar = async () => {
    if (!ticker) return setMensaje('Elegí un ticker')
    if (!ratio || ratio <= 0) return setMensaje('El ratio debe ser mayor a 0')
    setGuardando(true)
    setMensaje('')
    try {
      await crearSplit({ ticker, fecha: fechaSplit, ratio, nota: nota.trim() })
      setTicker('')
      setRatio(null)
      setNota('')
      cargar()
      alCambiar()
    } catch (error) {
      const texto = error instanceof Error ? error.message : ''
      setMensaje(
        texto.includes('409') ? 'Ya hay un split de ese papel en esa fecha' : 'No se pudo guardar',
      )
    } finally {
      setGuardando(false)
    }
  }

  const borrar = async (id: number) => {
    await eliminarSplit(id)
    cargar()
    alCambiar()
  }

  return (
    <div className="fondo-panel-splits" onClick={alCerrar}>
      <div className="panel-splits" onClick={(evento) => evento.stopPropagation()}>
        <div className="cabecera-panel-splits">
          <span>Splits de acciones</span>
          <button type="button" className="cerrar-formulario" onClick={alCerrar}>
            ×
          </button>
        </div>

        <p className="ayuda-splits">
          Un split cambia la cantidad de papeles sin mover plata: si tenías 100 y hay un split
          3:1, pasás a tener 300 y cada uno vale un tercio. El costo total no cambia y las
          tenencias se recalculan solas.
        </p>

        <div className="alta-split">
          <label className="campo-split">
            <span>Papel</span>
            {ticker ? (
              <span className="ticker-elegido">
                <LogoTicker ticker={ticker} tamano={18} />
                {ticker}
                <button type="button" onClick={() => setTicker('')}>
                  ×
                </button>
              </span>
            ) : (
              <span className="buscador-ticker-split">
                <input
                  value={busqueda}
                  placeholder="Buscar…"
                  onChange={(evento) => setBusqueda(evento.target.value.toUpperCase())}
                />
                {candidatos.length > 0 && (
                  <ul className="sugerencias-ticker">
                    {candidatos.map((simbolo) => (
                      <li key={simbolo}>
                        <button
                          type="button"
                          onClick={() => {
                            setTicker(simbolo)
                            setBusqueda('')
                          }}
                        >
                          <LogoTicker ticker={simbolo} tamano={16} />
                          {simbolo}
                        </button>
                      </li>
                    ))}
                  </ul>
                )}
              </span>
            )}
          </label>

          <label className="campo-split">
            <span>Fecha</span>
            <input
              type="date"
              value={fechaSplit}
              onChange={(evento) => setFechaSplit(evento.target.value)}
            />
          </label>

          <label className="campo-split angosto">
            <span>Ratio</span>
            <InputNumero valor={ratio} placeholder="3" alCambiar={setRatio} />
          </label>
        </div>

        {ratio !== null && ratio > 0 && (
          <span className="ratio-explicado">{describirRatio(ratio)}</span>
        )}

        <label className="campo-split">
          <span>Nota</span>
          <input
            value={nota}
            placeholder="Opcional"
            onChange={(evento) => setNota(evento.target.value)}
          />
        </label>

        {mensaje && <span className="mensaje-split">{mensaje}</span>}

        <button
          type="button"
          className="boton-guardar-operacion"
          disabled={guardando}
          onClick={() => void guardar()}
        >
          {guardando ? 'Guardando…' : 'Registrar split'}
        </button>

        {splits.length > 0 && (
          <ul className="lista-splits">
            {splits.map((split) => (
              <li key={split.id}>
                <LogoTicker ticker={split.ticker} tamano={16} />
                <span className="ticker-split">{split.ticker}</span>
                <span className="ratio-split">
                  {split.ratio >= 1 ? `${split.ratio}:1` : `1:${Math.round(1 / split.ratio)}`}
                </span>
                <span className="fecha-split">{fecha(split.fecha)}</span>
                {split.nota && <span className="nota-split">{split.nota}</span>}
                <button
                  type="button"
                  className="borrar-split"
                  title="Borrar split"
                  onClick={() => void borrar(split.id)}
                >
                  🗑
                </button>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  )
}

export default PanelSplits
