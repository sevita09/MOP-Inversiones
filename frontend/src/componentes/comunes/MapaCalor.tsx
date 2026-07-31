import './MapaCalor.css'

export interface FilaResumen {
  etiqueta: string
  valores: (number | null)[]
  /** Formato propio (el % de años positivos no se lee como un retorno) */
  formato?: (valor: number) => string
  /** Valor a partir del cual el número se pinta de verde. Cero para un retorno;
   *  50 para una proporción, donde lo que importa es si supera la mitad. */
  centro?: number
}

interface Props {
  columnas: string[]
  filas: (string | number)[]
  /** Una fila por cada elemento de `filas`, una celda por cada columna */
  valores: (number | null)[][]
  /** El |valor| donde el color satura; más allá no se distingue más */
  extremo: number
  formato: (valor: number) => string
  /** Columna extra a la derecha (el total del año) */
  totales?: (number | null)[]
  tituloTotales?: string
  /** Filas al pie con las estadísticas de cada columna */
  resumen?: FilaResumen[]
  /** Texto del tooltip de cada celda */
  descripcion?: (fila: string | number, columna: string, valor: number) => string
}

const VERDE = '63, 185, 80'
const ROJO = '248, 81, 73'
// Tope de opacidad: más arriba el número deja de leerse sobre el fondo
const OPACIDAD_MAXIMA = 0.72

/** Clase del número según de qué lado del centro cae. */
function claseValor(valor: number | null, centro = 0): string {
  if (valor === null) return ''
  return valor >= centro ? ' valor-positivo' : ' valor-negativo'
}

/** Color de una celda: escala divergente con el neutro del fondo en el cero.
 *
 *  No hay un tono en el medio —el cero es el fondo de la tabla—, que es lo que
 *  distingue una escala divergente de un arcoíris: la intensidad dice cuánto y
 *  el tono dice para qué lado. */
function fondo(valor: number | null, extremo: number): string | undefined {
  if (valor === null || extremo <= 0) return undefined
  const intensidad = Math.min(Math.abs(valor) / extremo, 1) * OPACIDAD_MAXIMA
  return `rgba(${valor >= 0 ? VERDE : ROJO}, ${intensidad.toFixed(3)})`
}

/** Mapa de calor reutilizable: estacionalidad (v8.2) y correlaciones (v8.3).
 *
 *  El valor va **escrito en cada celda**, no solo en el color: verde y rojo son
 *  casi el mismo color en daltonismo deutan (ΔE 2,2), así que el número es el
 *  que carga el dato y el fondo solo lo refuerza. */
function MapaCalor({
  columnas,
  filas,
  valores,
  extremo,
  formato,
  totales,
  tituloTotales = 'Año',
  resumen,
  descripcion,
}: Props) {
  return (
    <div className="mapa-calor-contenedor">
      <table className="mapa-calor">
        <thead>
          <tr>
            <th className="esquina" />
            {columnas.map((columna) => (
              <th key={columna}>{columna}</th>
            ))}
            {totales && <th className="columna-total">{tituloTotales}</th>}
          </tr>
        </thead>
        <tbody>
          {filas.map((fila, indiceFila) => (
            <tr key={fila}>
              <th className="etiqueta-fila">{fila}</th>
              {columnas.map((columna, indiceColumna) => {
                const valor = valores[indiceFila]?.[indiceColumna] ?? null
                return (
                  <td
                    key={columna}
                    style={{ backgroundColor: fondo(valor, extremo) }}
                    title={
                      valor !== null && descripcion
                        ? descripcion(fila, columna, valor)
                        : undefined
                    }
                  >
                    {valor === null ? '' : formato(valor)}
                  </td>
                )
              })}
              {totales && (
                <td className={`columna-total${claseValor(totales[indiceFila])}`}>
                  {totales[indiceFila] === null ? '' : formato(totales[indiceFila] as number)}
                </td>
              )}
            </tr>
          ))}
        </tbody>
        {resumen && resumen.length > 0 && (
          <tfoot>
            {resumen.map((fila) => (
              <tr key={fila.etiqueta}>
                <th className="etiqueta-fila">{fila.etiqueta}</th>
                {fila.valores.map((valor, indice) => (
                  <td key={columnas[indice]} className={claseValor(valor, fila.centro)}>
                    {valor === null ? '' : (fila.formato ?? formato)(valor)}
                  </td>
                ))}
                {totales && <td className="columna-total" />}
              </tr>
            ))}
          </tfoot>
        )}
      </table>
    </div>
  )
}

export default MapaCalor
