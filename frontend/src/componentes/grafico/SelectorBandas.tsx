import './SelectorBandas.css'

interface Props {
  mostrar: boolean
  alCambiar: (mostrar: boolean) => void
}

function SelectorBandas({ mostrar, alCambiar }: Props) {
  return (
    <button
      type="button"
      title="Bandas σ: ±1/2/3 desvíos del precio respecto a la EMA central (zonas de sobreextensión)"
      className={`boton-bandas${mostrar ? ' activo' : ''}`}
      onClick={() => alCambiar(!mostrar)}
    >
      σ
    </button>
  )
}

export default SelectorBandas
