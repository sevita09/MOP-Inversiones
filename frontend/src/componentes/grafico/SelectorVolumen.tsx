import './SelectorVolumen.css'

interface Props {
  mostrar: boolean
  alCambiar: (mostrar: boolean) => void
}

function SelectorVolumen({ mostrar, alCambiar }: Props) {
  return (
    <button
      type="button"
      title={mostrar ? 'Ocultar volumen' : 'Mostrar volumen'}
      className={`boton-volumen${mostrar ? ' activo' : ''}`}
      onClick={() => alCambiar(!mostrar)}
    >
      Vol
    </button>
  )
}

export default SelectorVolumen
