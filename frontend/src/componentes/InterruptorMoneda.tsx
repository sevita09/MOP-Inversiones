import { usarMoneda } from '../contextos/MonedaContext'
import { usarMonedaEfectiva } from '../hooks/usarMonedaEfectiva'
import { usarDolar } from '../hooks/usarDolar'
import './InterruptorMoneda.css'

function formatearCCL(valor: number): string {
  return valor.toLocaleString('es-AR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

// Cotización del CCL (ítem propio de la barra, para que respete la distribución)
export function CotizacionCCL() {
  const dolar = usarDolar()
  if (!dolar?.ccl) return null
  return (
    <span className="cotizacion-ccl" title={`CCL al ${dolar.ccl.fecha}`}>
      CCL ${formatearCCL(dolar.ccl.valor)}
    </span>
  )
}

// Interruptor ARS/USD (ítem propio de la barra)
function InterruptorMoneda() {
  const { alternarMoneda } = usarMoneda()
  const { moneda, fija } = usarMonedaEfectiva()

  return (
    <button
      type="button"
      className="interruptor-moneda"
      onClick={alternarMoneda}
      disabled={fija}
      title={fija ? 'Este ticker cotiza en una sola moneda' : 'Cambiar moneda de visualización'}
    >
      <span className={moneda === 'ARS' ? 'moneda-activa' : ''}>ARS</span>
      <span className="separador-moneda">/</span>
      <span className={moneda === 'USD' ? 'moneda-activa' : ''}>USD</span>
    </button>
  )
}

export default InterruptorMoneda
