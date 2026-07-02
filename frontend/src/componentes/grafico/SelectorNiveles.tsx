import './SelectorNiveles.css'

interface Props {
  mostrar: boolean
  alCambiar: (mostrar: boolean) => void
}

function SelectorNiveles({ mostrar, alCambiar }: Props) {
  return (
    <button
      type="button"
      title="Soporte/resistencia por swings; superpone los niveles fuertes de semanal y mensual"
      className={`boton-niveles${mostrar ? ' activo' : ''}`}
      onClick={() => alCambiar(!mostrar)}
    >
      S/R
    </button>
  )
}

export default SelectorNiveles
