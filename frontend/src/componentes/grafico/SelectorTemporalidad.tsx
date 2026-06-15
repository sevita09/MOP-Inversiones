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
  disponibles?: Temporalidad[]
}

function SelectorTemporalidad({ temporalidad, alCambiar, disponibles }: Props) {
  const opciones = disponibles
    ? TEMPORALIDADES.filter(({ valor }) => disponibles.includes(valor))
    : TEMPORALIDADES
  return (
    <div className="selector-temporalidad">
      {opciones.map(({ valor, etiqueta }) => (
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
