import { useEffect, useRef, useState } from 'react'
import { OSCILADORES, ORDEN_OSCILADORES } from './configOsciladores'
import type { NombreOscilador } from './configOsciladores'
import { aperturaOscilador, type AperturaConfig } from './config/estilosIndicadores'
import './MenuIndicadores.css'

interface Props {
  activos: Set<NombreOscilador>
  alAlternar: (nombre: NombreOscilador, activo: boolean) => void
  alConfigurar: (apertura: AperturaConfig) => void
}

function MenuIndicadores({ activos, alAlternar, alConfigurar }: Props) {
  const [abierto, setAbierto] = useState(false)
  const ref = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (!abierto) return
    const cerrar = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) setAbierto(false)
    }
    document.addEventListener('mousedown', cerrar)
    return () => document.removeEventListener('mousedown', cerrar)
  }, [abierto])

  return (
    <div className="menu-indicadores" ref={ref}>
      <button
        type="button"
        className={`boton-indicadores${activos.size > 0 ? ' activo' : ''}`}
        onClick={() => setAbierto(!abierto)}
      >
        Indicadores{activos.size > 0 ? ` (${activos.size})` : ''}
      </button>
      {abierto && (
        <div className="menu-indicadores-lista">
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
