import type { MotivoSalida, TradeBacktest } from '../../api/tipos'
import './TablaTrades.css'

interface Props {
  trades: TradeBacktest[]
  moneda: string
}

// Qué cerró la operación. Los de gestión de riesgo se marcan bien claros:
// leer la columna alcanza para ver si el riesgo actuó y de qué forma.
const NOMBRE_MOTIVO: Record<MotivoSalida, string> = {
  senal: 'Señal de salida',
  stop: 'Stop loss',
  trailing: 'Trailing stop',
  take_profit: 'Take profit',
  fin: 'Abierta al final',
}

const AYUDA_MOTIVO: Record<MotivoSalida, string> = {
  senal: 'Cerró porque se cumplieron las reglas de salida',
  stop: 'Cerró por gestión de riesgo: saltó el stop loss',
  trailing: 'Cerró por gestión de riesgo: saltó el trailing stop',
  take_profit: 'Cerró por gestión de riesgo: llegó al take profit',
  fin: 'Seguía abierta al terminar el período; se valuó al último cierre',
}

function fecha(ts: number): string {
  return new Date(ts * 1000).toLocaleDateString('es-AR', {
    day: '2-digit',
    month: '2-digit',
    year: '2-digit',
  })
}

function precio(valor: number): string {
  return valor.toLocaleString('es-AR', { maximumFractionDigits: 2 })
}

function duracion(dias: number): string {
  if (dias < 60) return `${Math.round(dias)} d`
  return `${(dias / 30.44).toFixed(1)} m`
}

/** Acumulado tras cada operación, COMPUESTO (cada trade reinvierte lo anterior):
 *  sumar los % daría un número inflado que no coincide con la curva de capital. */
function acumulados(trades: TradeBacktest[]): number[] {
  let factor = 1
  return trades.map((trade) => {
    factor *= 1 + trade.pnl_pct / 100
    return (factor - 1) * 100
  })
}

/** Tabla de operaciones del backtest: entrada, salida, duración y resultado. */
function TablaTrades({ trades, moneda }: Props) {
  if (trades.length === 0) {
    return <p className="trades-vacio">La estrategia no operó en este período.</p>
  }

  const acumulado = acumulados(trades)

  return (
    <div className="tabla-trades-contenedor">
      <table className="tabla-trades">
        <thead>
          <tr>
            <th>Entrada</th>
            <th>Salida</th>
            <th>Precio {moneda}</th>
            <th>Duración</th>
            <th>Motivo</th>
            <th>Resultado</th>
            <th title="Ganancia o pérdida acumulada desde el inicio, componiendo cada operación">
              Acumulado
            </th>
          </tr>
        </thead>
        <tbody>
          {trades.map((trade, i) => (
            <tr key={i} className={trade.gana ? 'gana' : 'pierde'}>
              <td>{fecha(trade.entrada_ts)}</td>
              <td>{fecha(trade.salida_ts)}</td>
              <td className="numero">
                {precio(trade.entrada_precio)} → {precio(trade.salida_precio)}
              </td>
              <td className="numero">{duracion(trade.duracion_dias)}</td>
              <td>
                <span className={`chip-motivo ${trade.motivo}`} title={AYUDA_MOTIVO[trade.motivo]}>
                  {NOMBRE_MOTIVO[trade.motivo]}
                </span>
              </td>
              <td className="numero resultado">
                {trade.pnl_pct > 0 ? '+' : ''}
                {trade.pnl_pct.toFixed(1)}%
              </td>
              <td className={`numero acumulado${acumulado[i] >= 0 ? ' positivo' : ' negativo'}`}>
                {acumulado[i] > 0 ? '+' : ''}
                {acumulado[i].toFixed(1)}%
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

export default TablaTrades
