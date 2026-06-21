import type { TipoHerramienta } from './tipos'
import './BarraHerramientas.css'

interface ItemHerramienta {
  tipo: TipoHerramienta
  etiqueta: string
  icono: string
}

const HERRAMIENTAS: ItemHerramienta[] = [
  { tipo: 'horizontal', etiqueta: 'Línea horizontal', icono: '─' },
  { tipo: 'tendencia', etiqueta: 'Línea de tendencia', icono: '╱' },
  { tipo: 'fibonacci', etiqueta: 'Fibonacci', icono: 'Fib' },
  { tipo: 'medicion', etiqueta: 'Medir rango', icono: '⇕' },
]

// Herramientas con renderizado implementado; el resto se muestra deshabilitado
const IMPLEMENTADAS = new Set<TipoHerramienta>([
  'horizontal',
  'tendencia',
  'fibonacci',
  'medicion',
])

interface Props {
  activa: TipoHerramienta
  alSeleccionar: (tipo: TipoHerramienta) => void
  alBorrarTodo: () => void
}

function BarraHerramientas({ activa, alSeleccionar, alBorrarTodo }: Props) {
  return (
    <div className="barra-herramientas">
      {HERRAMIENTAS.map((h) => {
        const disponible = IMPLEMENTADAS.has(h.tipo)
        return (
          <button
            key={h.tipo}
            type="button"
            disabled={!disponible}
            title={disponible ? h.etiqueta : `${h.etiqueta} (próximamente)`}
            className={`boton-herramienta${activa === h.tipo ? ' activo' : ''}`}
            onClick={() => alSeleccionar(activa === h.tipo ? null : h.tipo)}
          >
            {h.icono}
          </button>
        )
      })}
      <div className="separador-herramientas" />
      <button
        type="button"
        title="Borrar todos los dibujos"
        className="boton-herramienta boton-borrar"
        onClick={alBorrarTodo}
      >
        ✕
      </button>
    </div>
  )
}

export default BarraHerramientas
