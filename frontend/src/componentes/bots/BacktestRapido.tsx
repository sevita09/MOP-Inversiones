import { useState } from 'react'
import { backtestRapido } from '../../api/cliente'
import type {
  CapitalBot,
  Moneda,
  ReglasBot,
  ResultadoBacktest,
  RiesgoBot,
  TemporalidadBot,
} from '../../api/tipos'
import { reglasConContenido } from './configReglas'
import './BacktestRapido.css'

interface Props {
  ticker: string
  temporalidad: TemporalidadBot
  moneda: Moneda
  capital: CapitalBot
  riesgo: RiesgoBot
  reglas: ReglasBot
}

const MESES = 12

/** Prueba rápida de la estrategia del editor sobre el último año, sin guardar. */
function BacktestRapido({ ticker, temporalidad, moneda, capital, riesgo, reglas }: Props) {
  const [resultado, setResultado] = useState<ResultadoBacktest | null>(null)
  const [corriendo, setCorriendo] = useState(false)
  const [error, setError] = useState('')

  if (!ticker || !reglasConContenido(reglas)) return null

  const correr = async () => {
    setCorriendo(true)
    setError('')
    try {
      setResultado(
        await backtestRapido({
          ticker,
          temporalidad,
          moneda,
          capital,
          riesgo,
          reglas,
          meses: MESES,
        }),
      )
    } catch {
      setError('No se pudo correr la prueba')
      setResultado(null)
    } finally {
      setCorriendo(false)
    }
  }

  const metricas = resultado?.estrategia.metricas
  const pct = (valor: number) => `${valor > 0 ? '+' : ''}${valor.toFixed(1)}%`

  return (
    <div className="backtest-rapido">
      <button type="button" className="boton-probar" disabled={corriendo} onClick={() => void correr()}>
        {corriendo ? 'Probando…' : `⏱ Probar sobre el último año`}
      </button>

      {error && <span className="error-rapido">{error}</span>}

      {metricas && resultado && (
        <div className="resumen-rapido">
          <span
            className={`retorno-rapido${metricas.retorno_pct >= 0 ? ' positivo' : ' negativo'}`}
            title="Retorno de la estrategia en el último año"
          >
            {pct(metricas.retorno_pct)}
          </span>
          <span className="dato-rapido" title="Retorno del Buy & Hold en el mismo período">
            B&amp;H {pct(resultado.buy_and_hold.metricas.retorno_pct)}
          </span>
          <span className="dato-rapido" title="Operaciones cerradas">
            {metricas.trades_total} ops
          </span>
          {metricas.win_rate_pct !== null && (
            <span className="dato-rapido" title="Porcentaje de operaciones ganadoras">
              {metricas.win_rate_pct.toFixed(0)}% aciertos
            </span>
          )}
          <span className="dato-rapido" title="Peor caída del capital desde un pico">
            DD {metricas.drawdown_maximo_pct.toFixed(1)}%
          </span>
        </div>
      )}
    </div>
  )
}

export default BacktestRapido
