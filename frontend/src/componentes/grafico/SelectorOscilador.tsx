import './SelectorOscilador.css'

interface Props {
  etiqueta: string
  activo: boolean
  alCambiar: (activo: boolean) => void
}

function SelectorOscilador({ etiqueta, activo, alCambiar }: Props) {
  return (
    <button
      type="button"
      title={activo ? `Ocultar ${etiqueta}` : `Mostrar ${etiqueta}`}
      className={`boton-oscilador${activo ? ' activo' : ''}`}
      onClick={() => alCambiar(!activo)}
    >
      {etiqueta}
    </button>
  )
}

export default SelectorOscilador
