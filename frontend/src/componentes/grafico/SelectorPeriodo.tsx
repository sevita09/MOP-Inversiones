import './SelectorPeriodo.css'

const PERIODOS: { etiqueta: string; meses: number | null }[] = [
  { etiqueta: '1M', meses: 1 },
  { etiqueta: '3M', meses: 3 },
  { etiqueta: '6M', meses: 6 },
  { etiqueta: '1A', meses: 12 },
  { etiqueta: 'Todo', meses: null },
]

interface Props {
  alElegir: (meses: number | null) => void
}

function SelectorPeriodo({ alElegir }: Props) {
  return (
    <div className="selector-periodo">
      {PERIODOS.map(({ etiqueta, meses }) => (
        <button
          key={etiqueta}
          type="button"
          className="boton-periodo"
          onClick={() => alElegir(meses)}
        >
          {etiqueta}
        </button>
      ))}
    </div>
  )
}

export default SelectorPeriodo
