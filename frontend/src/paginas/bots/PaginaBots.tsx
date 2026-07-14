import { useState } from 'react'
import type { Bot } from '../../api/tipos'
import LogoTicker from '../../componentes/LogoTicker'
import FormularioBot from '../../componentes/bots/FormularioBot'
import { usarBots } from '../../hooks/usarBots'
import './PaginaBots.css'

const NOMBRE_TEMPORALIDAD = { D: 'Diario', S: 'Semanal', M: 'Mensual' }

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
              <div className="acciones-bot">
                <button
                  type="button"
                  title={bot.activo ? 'Pausar' : 'Reanudar'}
                  onClick={() => void alternarActivo(bot)}
                >
                  {bot.activo ? '⏸' : '▶'}
                </button>
                <button type="button" title="Editar" onClick={() => setFormulario(bot)}>
                  ✎
                </button>
                <button type="button" title="Duplicar" onClick={() => void duplicar(bot.id)}>
                  ⧉
                </button>
                <button
                  type="button"
                  title="Borrar"
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
