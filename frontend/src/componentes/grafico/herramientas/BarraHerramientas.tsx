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
  haySeleccion: boolean
  alConfigurar: () => void
  iman: boolean
  alAlternarIman: () => void
}

function BarraHerramientas({
  activa,
  alSeleccionar,
  alBorrarTodo,
  haySeleccion,
  alConfigurar,
  iman,
  alAlternarIman,
}: Props) {
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
        title={`Imán: engancha los dibujos a la apertura/cierre de la vela (${iman ? 'activo' : 'inactivo'})`}
        className={`boton-herramienta${iman ? ' activo' : ''}`}
        onClick={alAlternarIman}
      >
        <span className="iman-glifo">🧲</span>
      </button>
      {haySeleccion && (
        <button
          type="button"
          title="Estilo del dibujo seleccionado"
          className="boton-herramienta"
          onClick={alConfigurar}
        >
          ⚙
        </button>
      )}
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
