import type { TipoLinea } from '../../../contextos/EstilosContext'
import './config.css'

const ANCHOS = [1, 2, 3, 4]
const TIPOS: { valor: TipoLinea; muestra: string; titulo: string }[] = [
  { valor: 'solid', muestra: '───', titulo: 'Sólida' },
  { valor: 'dashed', muestra: '– – –', titulo: 'Guiones' },
  { valor: 'dotted', muestra: '· · ·', titulo: 'Puntos' },
]

interface Props {
  ancho: number
  tipoLinea: TipoLinea
  alCambiarAncho: (ancho: number) => void
  alCambiarTipo: (tipo: TipoLinea) => void
}

function SelectorLinea({ ancho, tipoLinea, alCambiarAncho, alCambiarTipo }: Props) {
  return (
    <div className="selector-linea">
      <div className="grupo-linea">
        {ANCHOS.map((a) => (
          <button
            key={a}
            type="button"
            className={a === ancho ? 'boton-linea activa' : 'boton-linea'}
            onClick={() => alCambiarAncho(a)}
          >
            {a}px
          </button>
        ))}
      </div>
      <div className="grupo-linea">
        {TIPOS.map(({ valor, muestra, titulo }) => (
          <button
            key={valor}
            type="button"
            title={titulo}
            className={valor === tipoLinea ? 'boton-linea activa' : 'boton-linea'}
            onClick={() => alCambiarTipo(valor)}
          >
            {muestra}
          </button>
        ))}
      </div>
    </div>
  )
}

export default SelectorLinea
