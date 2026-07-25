import type { MetricasBacktest } from '../../api/tipos'
import './PanelMetricas.css'

interface Props {
  estrategia: MetricasBacktest
  buyAndHold: MetricasBacktest
}

function pct(valor: number | null): string {
  if (valor === null) return '—'
  return `${valor > 0 ? '+' : ''}${valor.toFixed(1)}%`
}

function num(valor: number | null, decimales = 2): string {
  return valor === null ? '—' : valor.toFixed(decimales)
}

/** Ficha con el retorno destacado y el resto de las métricas del backtest. */
function PanelMetricas({ estrategia, buyAndHold }: Props) {
  const gana = estrategia.retorno_pct >= buyAndHold.retorno_pct

  const secundarias: { etiqueta: string; valor: string; ayuda: string }[] = [
    {
      etiqueta: 'Operaciones',
      valor: String(estrategia.trades_total),
      ayuda: 'Cantidad de trades cerrados en el período',
    },
    {
      etiqueta: 'Aciertos',
      valor: estrategia.win_rate_pct === null ? '—' : `${estrategia.win_rate_pct.toFixed(0)}%`,
      ayuda: 'Porcentaje de operaciones que cerraron en ganancia',
    },
    {
      etiqueta: 'Drawdown máx.',
      valor: pct(estrategia.drawdown_maximo_pct),
      ayuda: 'La peor caída del capital desde un pico: cuánto había que aguantar',
    },
    {
      etiqueta: 'Resultado medio',
      valor: pct(estrategia.expectancy_pct),
      ayuda: 'Expectancy: resultado promedio por operación',
    },
    {
      etiqueta: 'Profit factor',
      valor: num(estrategia.profit_factor),
      ayuda: 'Ganancia bruta dividida la pérdida bruta. Arriba de 1 gana plata',
    },
    {
      etiqueta: 'Sharpe',
      valor: num(estrategia.sharpe),
      ayuda: 'Retorno ajustado por volatilidad, anualizado',
    },
    {
      etiqueta: 'Sortino',
      valor: num(estrategia.sortino),
      ayuda: 'Como el Sharpe pero castigando solo la volatilidad a la baja',
    },
    {
      etiqueta: 'Exposición',
      valor: `${estrategia.exposicion_pct.toFixed(0)}%`,
      ayuda: 'Porcentaje del tiempo con posición abierta',
    },
    {
      etiqueta: 'Racha perdedora',
      valor: String(estrategia.racha_maxima_perdidas),
      ayuda: 'Máximo de operaciones perdedoras seguidas',
    },
  ]

  return (
    <div className="panel-metricas">
      <div className="retornos-backtest">
        <div className={`retorno-principal${estrategia.retorno_pct >= 0 ? '' : ' negativo'}`}>
          <span className="etiqueta-retorno">Estrategia</span>
          <strong>{pct(estrategia.retorno_pct)}</strong>
        </div>
        <div className="retorno-comparado">
          <span className="etiqueta-retorno">Buy &amp; Hold</span>
          <strong>{pct(buyAndHold.retorno_pct)}</strong>
        </div>
        <span className={`veredicto${gana ? ' gana' : ' pierde'}`}>
          {gana ? '↑ le gana al Buy & Hold' : '↓ no le gana al Buy & Hold'}
        </span>
      </div>

      <div className="grilla-metricas">
        {secundarias.map(({ etiqueta, valor, ayuda }) => (
          <div key={etiqueta} className="metrica" title={ayuda}>
            <span className="etiqueta-metrica">{etiqueta}</span>
            <span className="valor-metrica">{valor}</span>
          </div>
        ))}
      </div>
    </div>
  )
}

export default PanelMetricas
