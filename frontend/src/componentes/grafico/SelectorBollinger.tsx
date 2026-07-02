import './SelectorBollinger.css'

interface Props {
  mostrar: boolean
  alCambiar: (mostrar: boolean) => void
}

function SelectorBollinger({ mostrar, alCambiar }: Props) {
  return (
    <button
      type="button"
      title="Bandas de Bollinger: media móvil de 20 velas ± 2 desvíos estándar (volatilidad clásica)"
      className={`boton-bollinger${mostrar ? ' activo' : ''}`}
      onClick={() => alCambiar(!mostrar)}
    >
      BB
    </button>
  )
}

export default SelectorBollinger
