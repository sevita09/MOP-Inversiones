import './SelectorTenencia.css'

interface Props {
  mostrar: boolean
  alCambiar: (mostrar: boolean) => void
}

/** Marca sobre el gráfico todas las operaciones propias del papel. */
function SelectorOperaciones({ mostrar, alCambiar }: Props) {
  return (
    <button
      type="button"
      title="Mis operaciones: flecha verde en cada compra y roja en cada venta, al precio en que se ejecutó (incluye posiciones ya cerradas)"
      className={`boton-tenencia${mostrar ? ' activo' : ''}`}
      onClick={() => alCambiar(!mostrar)}
    >
      Ops
    </button>
  )
}

export default SelectorOperaciones
