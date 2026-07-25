import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { obtenerBot } from '../../api/cliente'
import type { Bot } from '../../api/tipos'
import LogoTicker from '../../componentes/LogoTicker'
import { crearSincronizadorTiempo } from '../../componentes/grafico/sincronizadorTiempo'
import CurvaCapital from '../../componentes/backtest/CurvaCapital'
import GraficoTrades from '../../componentes/backtest/GraficoTrades'
import PanelMetricas from '../../componentes/backtest/PanelMetricas'
import TablaTrades from '../../componentes/backtest/TablaTrades'
import { VENTANAS, usarBacktest } from '../../hooks/usarBacktest'
import './PaginaBacktest.css'

const NOMBRE_TEMPORALIDAD: Record<string, string> = { D: 'Diario', S: 'Semanal', M: 'Mensual' }

function fechaLarga(ts: number | null): string {
  if (ts === null) return '—'
  return new Date(ts * 1000).toLocaleDateString('es-AR', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
  })
}

function PaginaBacktest() {
  const { id } = useParams()
  const idBot = id ? Number(id) : null
  const [bot, setBot] = useState<Bot | null>(null)
  const [meses, setMeses] = useState<number | null>(null)
  const { resultado, cargando, error } = usarBacktest(idBot, meses)
  // Un solo sincronizador para los dos gráficos: mover uno mueve el otro
  const [sincronizador] = useState(crearSincronizadorTiempo)

  useEffect(() => {
    if (idBot === null) return
    obtenerBot(idBot)
      .then(setBot)
      .catch(() => setBot(null))
  }, [idBot])

  return (
    <div className="pagina-backtest">
      <div className="cabecera-backtest">
        <Link to="/bots" className="volver-bots">
          ← Bots
        </Link>
        {bot && (
          <div className="identidad-backtest">
            <LogoTicker ticker={bot.ticker} tamano={26} />
            <div>
              <h2>{bot.nombre}</h2>
              <span className="detalle-backtest">
                {bot.ticker} · {NOMBRE_TEMPORALIDAD[bot.temporalidad]} · {bot.moneda}
                {resultado && ` · ${fechaLarga(resultado.desde)} → ${fechaLarga(resultado.hasta)}`}
              </span>
            </div>
          </div>
        )}
        <div className="ventanas-backtest">
          {VENTANAS.map(({ etiqueta, meses: valor }) => (
            <button
              key={etiqueta}
              type="button"
              className={valor === meses ? 'chip-ventana activo' : 'chip-ventana'}
              onClick={() => setMeses(valor)}
            >
              {etiqueta}
            </button>
          ))}
        </div>
      </div>

      {cargando && <p className="estado-backtest">Corriendo el backtest…</p>}
      {error && <p className="estado-backtest error">{error}</p>}

      {resultado && !cargando && (
        <div className="cuerpo-backtest">
          <PanelMetricas
            estrategia={resultado.estrategia.metricas}
            buyAndHold={resultado.buy_and_hold.metricas}
          />

          <section className="seccion-backtest">
            <h3>Curva de capital</h3>
            <CurvaCapital
              estrategia={resultado.estrategia.curva}
              buyAndHold={resultado.buy_and_hold.curva}
              moneda={resultado.moneda}
              sincronizador={sincronizador}
            />
          </section>

          <section className="seccion-backtest">
            <h3>Operaciones sobre el gráfico</h3>
            <GraficoTrades
              ticker={resultado.ticker}
              temporalidad={resultado.temporalidad}
              moneda={resultado.moneda}
              trades={resultado.estrategia.trades}
              desde={resultado.desde}
              hasta={resultado.hasta}
              sincronizador={sincronizador}
            />
          </section>

          <section className="seccion-backtest">
            <h3>Operaciones ({resultado.estrategia.trades.length})</h3>
            <TablaTrades trades={resultado.estrategia.trades} moneda={resultado.moneda} />
          </section>
        </div>
      )}
    </div>
  )
}

export default PaginaBacktest
