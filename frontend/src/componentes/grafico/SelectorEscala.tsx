import type { EscalaPrecio } from '../../api/tipos'
import './SelectorEscala.css'

interface Props {
  escala: EscalaPrecio
  alCambiar: (escala: EscalaPrecio) => void
}

function SelectorEscala({ escala, alCambiar }: Props) {
  const esLog = escala === 'log'
  return (
    <button
      type="button"
      title={esLog ? 'Escala logarítmica' : 'Escala lineal'}
      className={`boton-escala${esLog ? ' activo' : ''}`}
      onClick={() => alCambiar(esLog ? 'lineal' : 'log')}
    >
      LOG
    </button>
  )
}

export default SelectorEscala
