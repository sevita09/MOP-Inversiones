import type { TipoGrafico } from '../../api/tipos'
import './SelectorTipoGrafico.css'

function Icono({ tipo }: { tipo: TipoGrafico }) {
  if (tipo === 'velas') {
    return (
      <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
        <rect x="3" y="2" width="1" height="12" />
        <rect x="1.5" y="4.5" width="4" height="6" rx="0.5" />
        <rect x="12" y="3" width="1" height="11" />
        <rect x="10.5" y="6" width="4" height="5" rx="0.5" />
      </svg>
    )
  }
  if (tipo === 'linea') {
    return (
      <svg width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.6">
        <polyline points="1,11 5,6 9,9 15,2" strokeLinejoin="round" strokeLinecap="round" />
      </svg>
    )
  }
  return (
    <svg width="16" height="16" viewBox="0 0 16 16">
      <path d="M1 11 L5 6 L9 9 L15 2 L15 14 L1 14 Z" fill="currentColor" opacity="0.35" />
      <polyline
        points="1,11 5,6 9,9 15,2"
        fill="none"
        stroke="currentColor"
        strokeWidth="1.6"
        strokeLinejoin="round"
        strokeLinecap="round"
      />
    </svg>
  )
}

const TIPOS: { valor: TipoGrafico; titulo: string }[] = [
  { valor: 'velas', titulo: 'Velas' },
  { valor: 'linea', titulo: 'Línea' },
  { valor: 'area', titulo: 'Área' },
]

interface Props {
  tipo: TipoGrafico
  alCambiar: (tipo: TipoGrafico) => void
}

function SelectorTipoGrafico({ tipo, alCambiar }: Props) {
  return (
    <div className="selector-tipo">
      {TIPOS.map(({ valor, titulo }) => (
        <button
          key={valor}
          type="button"
          title={titulo}
          className={`boton-tipo${valor === tipo ? ' activo' : ''}`}
          onClick={() => alCambiar(valor)}
        >
          <Icono tipo={valor} />
        </button>
      ))}
    </div>
  )
}

export default SelectorTipoGrafico
