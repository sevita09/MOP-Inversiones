import { useState } from 'react'
import { usarEstilos, type TipoLinea } from '../../../contextos/EstilosContext'
import SelectorColor from './SelectorColor'
import SelectorLinea from './SelectorLinea'
import type { AperturaConfig, ElementoEstilo } from './estilosIndicadores'
import './config.css'

interface Props {
  apertura: AperturaConfig
  alCerrar: () => void
}

/** Diálogo de estilo con pestañas (una por grupo: EMA/σ/BB, o una sola para un
 *  oscilador). Cada grupo tiene una o varias líneas. Aplica en vivo y guarda
 *  como default del usuario; el recomendado se muestra en gris con "Volver". */
function DialogoConfig({ apertura, alCerrar }: Props) {
  const { grupos, titulo } = apertura
  const { estiloDe, overrideDe, guardar, volver } = usarEstilos()
  const [activa, setActiva] = useState(0)
  const grupo = grupos[activa] ?? grupos[0]
  const hayOverride = grupo.elementos.some((e) => Object.keys(overrideDe(e.id)).length > 0)

  const seccion = (elem: ElementoEstilo) => {
    const ef = estiloDe(elem.id, elem.recomendado)
    return (
      <div className="seccion-config" key={elem.id}>
        {grupo.elementos.length > 1 && <div className="etiqueta-seccion">{elem.etiqueta}</div>}
        {elem.campos.includes('color') && (
          <div className="campo-config">
            <span className="etiqueta-config">Color</span>
            <SelectorColor
              valor={ef.color ?? '#ffffff'}
              alCambiar={(color) => guardar(elem.id, { color })}
            />
          </div>
        )}
        {elem.campos.includes('linea') && (
          <div className="campo-config">
            <span className="etiqueta-config">Línea</span>
            <SelectorLinea
              ancho={ef.ancho ?? 1}
              tipoLinea={(ef.tipoLinea ?? 'solid') as TipoLinea}
              alCambiarAncho={(ancho) => guardar(elem.id, { ancho })}
              alCambiarTipo={(tipoLinea) => guardar(elem.id, { tipoLinea })}
            />
          </div>
        )}
        <div className="recomendado-config">
          Recomendado: <b style={{ color: elem.recomendado.color }}>{elem.recomendado.color}</b>
          {elem.recomendado.ancho ? ` · ${elem.recomendado.ancho}px` : ''}
        </div>
      </div>
    )
  }

  return (
    <div className="fondo-config" onClick={alCerrar}>
      <div className="dialogo-config" onClick={(e) => e.stopPropagation()}>
        <div className="cabecera-config">
          <span>{titulo}</span>
          <button type="button" className="cerrar-config" onClick={alCerrar}>×</button>
        </div>

        {grupos.length > 1 && (
          <div className="pestanas-config">
            {grupos.map((g, i) => (
              <button
                key={g.titulo}
                type="button"
                className={i === activa ? 'pestana-config activa' : 'pestana-config'}
                onClick={() => setActiva(i)}
              >
                {g.titulo}
              </button>
            ))}
          </div>
        )}

        {grupo.elementos.map(seccion)}

        <div className="pie-config">
          <button
            type="button"
            className="volver-config"
            disabled={!hayOverride}
            onClick={() => grupo.elementos.forEach((e) => volver(e.id))}
          >
            Volver a lo recomendado
          </button>
        </div>
      </div>
    </div>
  )
}

export default DialogoConfig
