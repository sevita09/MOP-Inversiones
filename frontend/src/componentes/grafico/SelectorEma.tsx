import './SelectorEma.css'

interface Props {
  mostrar: boolean
  alCambiar: (mostrar: boolean) => void
}

function SelectorEma({ mostrar, alCambiar }: Props) {
  return (
    <button
      type="button"
      title={mostrar ? 'Ocultar EMA central' : 'Mostrar EMA central'}
      className={`boton-ema${mostrar ? ' activo' : ''}`}
      onClick={() => alCambiar(!mostrar)}
    >
      EMA
    </button>
  )
}

export default SelectorEma
