import type { Temporalidad } from '../../api/tipos'
import { usarEstilos } from '../../contextos/EstilosContext'
import {
  PARAMS_POR_INDICADOR,
  claveGuardada,
  recomendadoDe,
} from './config/paramsIndicadores'
import './SelectorEma.css'

interface Props {
  mostrar: boolean
  temporalidad: Temporalidad
  alCambiar: (mostrar: boolean) => void
}

// El período efectivo de la EMA central: el que el usuario haya fijado para esta
// temporalidad, o el recomendado (D=200, S=50, M=12) si no lo cambió.
function SelectorEma({ mostrar, temporalidad, alCambiar }: Props) {
  const { paramsDe } = usarEstilos()
  const campo = PARAMS_POR_INDICADOR.bandas[0]
  const override = paramsDe('bandas')[claveGuardada(campo, temporalidad)]
  const periodo = override ?? recomendadoDe(campo, temporalidad)
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
