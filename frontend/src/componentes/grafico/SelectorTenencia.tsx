import './SelectorTenencia.css'

interface Props {
  mostrar: boolean
  alCambiar: (mostrar: boolean) => void
}

/** Marca sobre el gráfico las compras abiertas de la cartera y el PPC. */
function SelectorTenencia({ mostrar, alCambiar }: Props) {
  return (
    <button
      type="button"
      title="Mis compras: marca en violeta el día y el precio de cada compra abierta (FIFO) y el precio promedio de compra"
      className={`boton-tenencia${mostrar ? ' activo' : ''}`}
      onClick={() => alCambiar(!mostrar)}
    >
      PPC
    </button>
  )
}

export default SelectorTenencia
