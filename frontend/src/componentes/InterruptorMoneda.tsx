import { usarMoneda } from '../contextos/MonedaContext'
import { usarMonedaEfectiva } from '../hooks/usarMonedaEfectiva'
import { usarDolar } from '../hooks/usarDolar'
import './InterruptorMoneda.css'

function formatearDolar(valor: number): string {
  return valor.toLocaleString('es-AR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

/** Cotización del MEP (ítem propio de la barra, para que respete la distribución).
 *
 *  Es informativa: el gráfico en dólares sigue convirtiendo con el CCL —el MEP
 *  se usa para valuar la cartera—, y el tooltip lo aclara. */
export function CotizacionDolar() {
  const dolar = usarDolar()
  if (!dolar?.mep) return null
  return (
    <span
      className="cotizacion-ccl"
      title={`MEP al ${dolar.mep.fecha} · el gráfico en dólares convierte con el CCL`}
    >
      MEP ${formatearDolar(dolar.mep.valor)}
    </span>
  )
}

/** Moneda de visualización: dice en cuál está y al tocarlo cambia a la otra.
 *
 *  Con tickers de una sola moneda (CEDEARs, índices del exterior, cripto,
 *  dólares) el botón queda inerte: no hay otra vista a la que ir. */
function InterruptorMoneda() {
  const { alternarMoneda } = usarMoneda()
  const { moneda, fija } = usarMonedaEfectiva()

  return (
    <span className="moneda-en-regla">
      <button
        type="button"
        className={`interruptor-moneda${fija ? ' fija' : ''}`}
        onClick={fija ? undefined : alternarMoneda}
        title={
          fija
            ? `Este ticker cotiza solo en ${moneda}`
            : `Ver en ${moneda === 'ARS' ? 'dólares' : 'pesos'}`
        }
      >
        {moneda}
      </button>
    </span>
  )
}

export default InterruptorMoneda
