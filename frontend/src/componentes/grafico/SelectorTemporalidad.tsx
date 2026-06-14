import type { Temporalidad } from '../../api/tipos'
import './SelectorTemporalidad.css'

const TEMPORALIDADES: { valor: Temporalidad; etiqueta: string }[] = [
  { valor: 'H', etiqueta: '1H' },
  { valor: 'D', etiqueta: '1D' },
  { valor: 'S', etiqueta: '1S' },
  { valor: 'M', etiqueta: '1M' },
]

interface Props {
  temporalidad: Temporalidad
  alCambiar: (temporalidad: Temporalidad) => void
}

function SelectorTemporalidad({ temporalidad, alCambiar }: Props) {
  return (
    <div className="selector-temporalidad">
      {TEMPORALIDADES.map(({ valor, etiqueta }) => (
        <button
          key={valor}
          type="button"
          className={`boton-temporalidad${valor === temporalidad ? ' activo' : ''}`}
          onClick={() => alCambiar(valor)}
        >
          {etiqueta}
        </button>
      ))}
    </div>
  )
}

export default SelectorTemporalidad
