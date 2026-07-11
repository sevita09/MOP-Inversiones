import type { Estilo, TipoLinea } from '../../../contextos/EstilosContext'
import SelectorColor, { nombreColor } from '../config/SelectorColor'
import SelectorLinea from '../config/SelectorLinea'
import '../config/config.css'

interface Props {
  titulo: string
  campos: ('color' | 'linea')[]
  estilo: Estilo // efectivo actual del dibujo (para mostrar seleccionado)
  recomendado: Estilo // recomendado del código (en gris)
  hayOverride: boolean
  alCambiar: (cambios: Estilo) => void
  alVolver: () => void
  alCerrar: () => void
}

/** Diálogo de estilo de un dibujo: color / ancho / tipo de línea. Guarda en el
 *  dibujo y como default de la herramienta; recomendado en gris + "Volver". */
function DialogoEstiloDibujo({
  titulo,
  campos,
  estilo,
  recomendado,
  hayOverride,
  alCambiar,
  alVolver,
  alCerrar,
}: Props) {
  return (
    <div className="fondo-config" onClick={alCerrar}>
      <div className="dialogo-config" onClick={(e) => e.stopPropagation()} style={{ minWidth: 260, width: 280 }}>
        <div className="cabecera-config">
          <span>{titulo}</span>
          <button type="button" className="cerrar-config" onClick={alCerrar}>×</button>
        </div>

        <div className="seccion-config">
          {campos.includes('color') && (
            <div className="campo-config">
              <span className="etiqueta-config">Color</span>
              <SelectorColor
                valor={estilo.color ?? '#ffffff'}
                alCambiar={(color) => alCambiar({ color })}
              />
            </div>
          )}
          {campos.includes('linea') && (
            <div className="campo-config">
              <span className="etiqueta-config">Línea</span>
              <SelectorLinea
                ancho={estilo.ancho ?? 1}
                tipoLinea={(estilo.tipoLinea ?? 'solid') as TipoLinea}
                alCambiarAncho={(ancho) => alCambiar({ ancho })}
                alCambiarTipo={(tipoLinea) => alCambiar({ tipoLinea })}
              />
            </div>
          )}
          <div className="recomendado-config">
            Recomendado:{' '}
            <b style={{ color: recomendado.color }}>{nombreColor(recomendado.color ?? '')}</b>
            {recomendado.ancho ? ` · ${recomendado.ancho}px` : ''}
          </div>
        </div>

        <div className="pie-config">
          <button type="button" className="volver-config" disabled={!hayOverride} onClick={alVolver}>
            Volver a lo recomendado
          </button>
        </div>
      </div>
    </div>
  )
}

export default DialogoEstiloDibujo
