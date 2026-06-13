import { usarMoneda } from '../contextos/MonedaContext'

function InterruptorMoneda() {
  const { moneda, alternarMoneda } = usarMoneda()

  return (
    <button
      type="button"
      className="interruptor-moneda"
      onClick={alternarMoneda}
      title="Cambiar moneda de visualización"
    >
      <span className={moneda === 'ARS' ? 'moneda-activa' : ''}>ARS</span>
      <span className="separador-moneda">/</span>
      <span className={moneda === 'USD' ? 'moneda-activa' : ''}>USD</span>
    </button>
  )
}

export default InterruptorMoneda
