import { useEffect, useRef, useState } from 'react'
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

/** Desplegable con el tipo de gráfico: un solo botón en la barra en vez de tres. */
function SelectorTipoGrafico({ tipo, alCambiar }: Props) {
  const [abierto, setAbierto] = useState(false)
  const [posicion, setPosicion] = useState({ top: 0, left: 0 })
  const ref = useRef<HTMLDivElement>(null)
  const botonRef = useRef<HTMLButtonElement>(null)

  useEffect(() => {
    if (!abierto) return
    const cerrar = (evento: MouseEvent) => {
      if (ref.current && !ref.current.contains(evento.target as Node)) setAbierto(false)
    }
    document.addEventListener('mousedown', cerrar)
    return () => document.removeEventListener('mousedown', cerrar)
  }, [abierto])

  const actual = TIPOS.find(({ valor }) => valor === tipo) ?? TIPOS[0]

  // El menú va con position:fixed anclado al botón: el overflow:hidden de la
  // barra (BarraOverflow) recorta cualquier desplegable absoluto
  const alternar = () => {
    const boton = botonRef.current
    if (!abierto && boton) {
      const rect = boton.getBoundingClientRect()
      // Centrado respecto del botón (el translateX(-50%) lo termina de ubicar)
      setPosicion({ top: rect.bottom + 4, left: rect.left + rect.width / 2 })
    }
    setAbierto(!abierto)
  }

  return (
    <div className="selector-tipo" ref={ref}>
      <button
        ref={botonRef}
        type="button"
        title={`Tipo de gráfico: ${actual.titulo}`}
        className={`boton-tipo desplegable${abierto ? ' activo' : ''}`}
        onClick={alternar}
      >
        <Icono tipo={actual.valor} />
        <span className="flecha-tipo">▾</span>
      </button>
      {abierto && (
        <div className="menu-tipo" style={posicion}>
          {TIPOS.map(({ valor, titulo }) => (
            <button
              key={valor}
              type="button"
              className={`opcion-tipo${valor === tipo ? ' activa' : ''}`}
              onClick={() => {
                alCambiar(valor)
                setAbierto(false)
              }}
            >
              <Icono tipo={valor} />
              {titulo}
            </button>
          ))}
        </div>
      )}
    </div>
  )
}

export default SelectorTipoGrafico
