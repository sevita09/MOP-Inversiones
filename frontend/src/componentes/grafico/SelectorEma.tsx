import type { Temporalidad } from '../../api/tipos'
import './SelectorEma.css'

// La EMA central depende de la temporalidad (misma metodología que el backend)
const PERIODO_EMA: Record<Temporalidad, number> = { H: 200, D: 200, S: 50, M: 12 }

interface Props {
  mostrar: boolean
  temporalidad: Temporalidad
  alCambiar: (mostrar: boolean) => void
}

function SelectorEma({ mostrar, temporalidad, alCambiar }: Props) {
  const periodo = PERIODO_EMA[temporalidad]
  return (
    <button
      type="button"
      title={`EMA ${periodo}: media móvil exponencial de ${periodo} velas — la tendencia central de la metodología`}
      className={`boton-ema${mostrar ? ' activo' : ''}`}
      onClick={() => alCambiar(!mostrar)}
    >
      EMA
    </button>
  )
}

export default SelectorEma
