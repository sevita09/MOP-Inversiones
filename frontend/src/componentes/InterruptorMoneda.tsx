import { usarMoneda } from '../contextos/MonedaContext'
import { usarMonedaEfectiva } from '../hooks/usarMonedaEfectiva'
import { usarDolar } from '../hooks/usarDolar'
import './InterruptorMoneda.css'

function formatearCCL(valor: number): string {
  return valor.toLocaleString('es-AR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

function InterruptorMoneda() {
  const { alternarMoneda } = usarMoneda()
  const { moneda, fija } = usarMonedaEfectiva()
  const dolar = usarDolar()

  return (
    <div className="moneda">
      {dolar?.ccl && (
        <span className="cotizacion-ccl" title={`CCL al ${dolar.ccl.fecha}`}>
          CCL ${formatearCCL(dolar.ccl.valor)}
        </span>
      )}
      <button
        type="button"
        className="interruptor-moneda"
        onClick={alternarMoneda}
        disabled={fija}
        title={
          fija
            ? 'Este ticker cotiza en una sola moneda'
            : 'Cambiar moneda de visualización'
        }
      >
        <span className={moneda === 'ARS' ? 'moneda-activa' : ''}>ARS</span>
        <span className="separador-moneda">/</span>
        <span className={moneda === 'USD' ? 'moneda-activa' : ''}>USD</span>
      </button>
    </div>
  )
}

export default InterruptorMoneda
