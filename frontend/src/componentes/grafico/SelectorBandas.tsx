import './SelectorBandas.css'

interface Props {
  mostrar: boolean
  alCambiar: (mostrar: boolean) => void
}

function SelectorBandas({ mostrar, alCambiar }: Props) {
  return (
    <button
      type="button"
      title={mostrar ? 'Ocultar bandas σ' : 'Mostrar bandas σ'}
      className={`boton-bandas${mostrar ? ' activo' : ''}`}
      onClick={() => alCambiar(!mostrar)}
    >
      σ
    </button>
  )
}

export default SelectorBandas
