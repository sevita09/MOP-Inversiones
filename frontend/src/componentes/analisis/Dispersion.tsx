import { useMemo } from 'react'
import type { PuntoDispersion } from '../../api/tipos'
import './Dispersion.css'

interface Props {
  puntos: PuntoDispersion[]
  a: string
  b: string
  /** La de la ventana vigente, que es lo que muestra la nube */
  correlacion: number | null
  periodo: string
}

const ANCHO = 300
const ALTO = 300
const MARGEN = 28

/** Nube de dispersión de los retornos diarios de dos papeles.
 *
 *  Es lo que hay detrás del número: la correlación resume la nube en un
 *  coeficiente, y la nube muestra lo que el coeficiente esconde —si la relación
 *  es pareja o la arman cuatro días extremos. */
function Dispersion({ puntos, a, b, correlacion, periodo }: Props) {
  const { escalados, limite } = useMemo(() => {
    const extremos = puntos.flatMap((p) => [Math.abs(p.a), Math.abs(p.b)])
    // Escala simétrica para que el cero quede en el centro exacto
    const tope = extremos.length ? Math.max(...extremos) : 0.01
    const util = (ANCHO - MARGEN * 2) / 2
    return {
      limite: tope,
      escalados: puntos.map((p) => ({
        x: ANCHO / 2 + (p.a / tope) * util,
        y: ALTO / 2 - (p.b / tope) * util,
      })),
    }
  }, [puntos])

  if (puntos.length === 0) return null

  return (
    <figure className="dispersion">
      <svg viewBox={`0 0 ${ANCHO} ${ALTO}`} role="img" aria-label={`Dispersión ${a} vs ${b}`}>
        {/* Ejes en el cero: los cuadrantes dicen si los días coinciden en signo */}
        <line x1={MARGEN} y1={ALTO / 2} x2={ANCHO - MARGEN} y2={ALTO / 2} className="eje" />
        <line x1={ANCHO / 2} y1={MARGEN} x2={ANCHO / 2} y2={ALTO - MARGEN} className="eje" />
        {escalados.map((punto, indice) => (
          <circle key={indice} cx={punto.x} cy={punto.y} r={2} className="punto" />
        ))}
        <text x={ANCHO - MARGEN} y={ALTO / 2 - 6} className="rotulo fin">
          {a} →
        </text>
        <text x={ANCHO / 2 + 6} y={MARGEN} className="rotulo">
          ↑ {b}
        </text>
      </svg>
      <figcaption>
        últimos {periodo} · {puntos.length.toLocaleString('es-AR')} datos · máximo ±
        {(limite * 100).toFixed(1)}%
        {correlacion !== null && ` · correlación ${correlacion.toFixed(2)}`}
      </figcaption>
    </figure>
  )
}

export default Dispersion
