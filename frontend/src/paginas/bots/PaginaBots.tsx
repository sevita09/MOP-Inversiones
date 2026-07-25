import { useState } from 'react'
import { Link } from 'react-router-dom'
import type { Bot } from '../../api/tipos'
import LogoTicker from '../../componentes/LogoTicker'
import FormularioBot from '../../componentes/bots/FormularioBot'
import { usarBots } from '../../hooks/usarBots'
import './PaginaBots.css'

const NOMBRE_TEMPORALIDAD = { D: 'Diario', S: 'Semanal', M: 'Mensual' }

/** Ícono de barras del backtest; hereda el color del botón (mismo gris que el resto). */
function IconoBacktest() {
  return (
    <svg width="15" height="15" viewBox="0 0 16 16" fill="currentColor" aria-hidden="true">
      <rect x="1.5" y="8" width="3" height="6" rx="0.5" />
      <rect x="6.5" y="4.5" width="3" height="9.5" rx="0.5" />
      <rect x="11.5" y="1.5" width="3" height="12.5" rx="0.5" />
    </svg>
  )
}

function PaginaBots() {
  const { bots, cargando, crear, editar, eliminar, duplicar, alternarActivo } = usarBots()
  const [formulario, setFormulario] = useState<'nuevo' | Bot | null>(null)
  const [borrando, setBorrando] = useState<Bot | null>(null)

  return (
    <div className="pagina-bots">
      <div className="cabecera-bots">
        <h2>Bots</h2>
        <button type="button" className="boton-nuevo-bot" onClick={() => setFormulario('nuevo')}>
          ＋ Nuevo bot
        </button>
      </div>

      {cargando && <p className="bots-vacio">Cargando…</p>}
      {!cargando && bots.length === 0 && (
        <div className="bots-vacio">
          <p>Todavía no hay bots.</p>
          <p className="nota-bots">
            Un bot vigila un ticker con reglas de entrada y salida y avisa cuando disparan.
          </p>
        </div>
      )}

      {bots.length > 0 && (
        <ul className="lista-bots">
          {bots.map((bot) => (
            <li key={bot.id} className={`fila-bot${bot.activo ? '' : ' pausado'}`}>
              <LogoTicker ticker={bot.ticker} tamano={26} />
              <div className="datos-bot">
                <span className="nombre-bot">{bot.nombre}</span>
                <span className="detalle-bot">
                  {bot.ticker} · {NOMBRE_TEMPORALIDAD[bot.temporalidad]} · {bot.moneda}
                  {!bot.activo && <span className="chip-pausado">pausado</span>}
                </span>
              </div>
              {bot.metricas && (
                <span className="metricas-bot" title="Resultado del último backtest">
                  <span
                    className={`retorno-bot${
                      bot.metricas.estrategia.retorno_pct >= 0 ? ' positivo' : ' negativo'
                    }`}
                  >
                    {bot.metricas.estrategia.retorno_pct > 0 ? '+' : ''}
                    {bot.metricas.estrategia.retorno_pct.toFixed(1)}%
                  </span>
                  <span
                    className={`veredicto-bot${
                      bot.metricas.estrategia.retorno_pct >= bot.metricas.buy_and_hold_retorno_pct
                        ? ' gana'
                        : ' pierde'
                    }`}
                    title={`Buy & Hold: ${
                      bot.metricas.buy_and_hold_retorno_pct > 0 ? '+' : ''
                    }${bot.metricas.buy_and_hold_retorno_pct.toFixed(1)}%`}
                  >
                    {bot.metricas.estrategia.retorno_pct >= bot.metricas.buy_and_hold_retorno_pct
                      ? '↑ le gana al B&H'
                      : '↓ no le gana al B&H'}
                  </span>
                </span>
              )}
              <div className="acciones-bot">
                <Link
                  to={`/bots/${bot.id}/backtest`}
                  className="accion-backtest"
                  data-tooltip="Ver resultados del backtest"
                >
                  <IconoBacktest />
                </Link>
                <button
                  type="button"
                  data-tooltip={bot.activo ? 'Pausar: deja de generar señales' : 'Reanudar: vuelve a generar señales'}
                  onClick={() => void alternarActivo(bot)}
                >
                  {bot.activo ? '⏸' : '▶'}
                </button>
                <button
                  type="button"
                  data-tooltip="Editar reglas y configuración"
                  onClick={() => setFormulario(bot)}
                >
                  ✎
                </button>
                <button
                  type="button"
                  data-tooltip="Duplicar: copia el bot con sus reglas"
                  onClick={() => void duplicar(bot.id)}
                >
                  ⧉
                </button>
                <button
                  type="button"
                  data-tooltip="Borrar este bot"
                  className="accion-borrar"
                  onClick={() => setBorrando(bot)}
                >
                  🗑
                </button>
              </div>
            </li>
          ))}
        </ul>
      )}

      {formulario && (
        <FormularioBot
          bot={formulario === 'nuevo' ? null : formulario}
          alGuardar={async (datos) => {
            if (formulario === 'nuevo') await crear(datos)
            else await editar(formulario.id, datos)
            setFormulario(null)
          }}
          alCerrar={() => setFormulario(null)}
        />
      )}

      {borrando && (
        <div className="fondo-confirmar" onClick={() => setBorrando(null)}>
          <div className="dialogo-confirmar" onClick={(evento) => evento.stopPropagation()}>
            <p>
              ¿Borrar el bot <strong>{borrando.nombre}</strong>?
            </p>
            <p className="nota-confirmar">Se pierden sus reglas. Esta acción no se deshace.</p>
            <div className="botones-confirmar">
              <button
                type="button"
                className="boton-borrar"
                onClick={() => {
                  void eliminar(borrando.id)
                  setBorrando(null)
                }}
              >
                Borrar
              </button>
              <button type="button" className="boton-cancelar" onClick={() => setBorrando(null)}>
                Cancelar
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default PaginaBots
