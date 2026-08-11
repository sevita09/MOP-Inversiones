import { useEffect, useRef, useState } from 'react'
import { OSCILADORES, ORDEN_OSCILADORES } from './configOsciladores'
import type { NombreOscilador } from './configOsciladores'
import { aperturaOscilador, type AperturaConfig } from './config/estilosIndicadores'
import './MenuIndicadores.css'

/** Una onda de oscilador entre sus dos niveles de referencia: es exactamente lo
 *  que el menú agrega bajo el precio (RSI con 30/70, estocástico con 20/80). */
const ICONO = (
  <svg viewBox="0 0 24 24" className="icono-indicadores" aria-hidden="true">
    <line x1="2" y1="7" x2="22" y2="7" className="nivel" />
    <line x1="2" y1="17" x2="22" y2="17" className="nivel" />
    <path d="M2 15 C5 15, 5.5 5, 8.5 5 S12 18, 15 18 S19 8, 22 8" className="onda" />
  </svg>
)

interface Props {
  activos: Set<NombreOscilador>
  alAlternar: (nombre: NombreOscilador, activo: boolean) => void
  alConfigurar: (apertura: AperturaConfig) => void
}

function MenuIndicadores({ activos, alAlternar, alConfigurar }: Props) {
  const [abierto, setAbierto] = useState(false)
  const [posicion, setPosicion] = useState({ top: 0, left: 0 })
  const ref = useRef<HTMLDivElement>(null)
  const botonRef = useRef<HTMLButtonElement>(null)

  useEffect(() => {
    if (!abierto) return
    const cerrar = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) setAbierto(false)
    }
    document.addEventListener('mousedown', cerrar)
    return () => document.removeEventListener('mousedown', cerrar)
  }, [abierto])

  // La lista va con position:fixed anclada al botón: el overflow:hidden de la
  // barra (BarraOverflow) recorta cualquier desplegable absoluto común.
  const alternar = () => {
    const boton = botonRef.current
    if (!abierto && boton) {
      const rect = boton.getBoundingClientRect()
      setPosicion({
        top: rect.bottom + 4,
        left: Math.min(rect.left, window.innerWidth - 180),
      })
    }
    setAbierto(!abierto)
  }

  return (
    <div className="menu-indicadores" ref={ref}>
      <button
        ref={botonRef}
        type="button"
        className={`boton-indicadores${activos.size > 0 ? ' activo' : ''}`}
        onClick={alternar}
        title="Indicadores"
        aria-label={
          activos.size > 0 ? `Indicadores (${activos.size} activos)` : 'Indicadores'
        }
      >
        {ICONO}
        {activos.size > 0 && <span className="conteo-indicadores">{activos.size}</span>}
      </button>
      {abierto && (
        <div className="menu-indicadores-lista" style={posicion}>
          {ORDEN_OSCILADORES.map((nombre) => (
            <div key={nombre} className="menu-indicadores-item">
              <label className="menu-indicadores-check" title={OSCILADORES[nombre].descripcion}>
                <input
                  type="checkbox"
                  checked={activos.has(nombre)}
                  onChange={(e) => alAlternar(nombre, e.target.checked)}
                />
                {OSCILADORES[nombre].titulo}
              </label>
              <button
                type="button"
                className="menu-indicadores-tuerca"
                title={`Configurar ${OSCILADORES[nombre].titulo}`}
                onClick={() => {
                  setAbierto(false)
                  alConfigurar(aperturaOscilador(nombre))
                }}
              >
                ⚙
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

export default MenuIndicadores
