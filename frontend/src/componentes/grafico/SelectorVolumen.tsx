import './SelectorVolumen.css'

interface Props {
  mostrar: boolean
  alCambiar: (mostrar: boolean) => void
}

function SelectorVolumen({ mostrar, alCambiar }: Props) {
  return (
    <button
      type="button"
      title="Volumen: cantidad de acciones operadas en cada vela"
      className={`boton-volumen${mostrar ? ' activo' : ''}`}
      onClick={() => alCambiar(!mostrar)}
    >
      Vol
    </button>
  )
}

export default SelectorVolumen
