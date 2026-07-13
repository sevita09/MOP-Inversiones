import './SelectorVPVR.css'

interface Props {
  mostrar: boolean
  alCambiar: (mostrar: boolean) => void
}

function SelectorVPVR({ mostrar, alCambiar }: Props) {
  return (
    <button
      type="button"
      title="Perfil de volumen del rango visible (VPVR): volumen por nivel de precio; el dorado es el POC"
      className={`boton-vpvr${mostrar ? ' activo' : ''}`}
      onClick={() => alCambiar(!mostrar)}
    >
      VP
    </button>
  )
}

export default SelectorVPVR
