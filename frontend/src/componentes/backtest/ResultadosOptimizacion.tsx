import type { ResultadoCombinacion, ResultadoOptimizacion } from '../../api/tipos'
import type { OpcionOptimizable } from './opcionesOptimizables'
import './ResultadosOptimizacion.css'

interface Props {
  resultado: ResultadoOptimizacion
  opciones: OpcionOptimizable[]
}

function num(valor: number | null, decimales = 2): string {
  return valor === null ? '—' : valor.toFixed(decimales)
}

function pct(valor: number): string {
  return `${valor > 0 ? '+' : ''}${valor.toFixed(1)}%`
}

/** Color de la celda según qué tan buena es respecto al rango de la grilla. */
function tonoCelda(metrica: number | null, minimo: number, maximo: number): string {
  if (metrica === null) return 'transparent'
  if (maximo === minimo) return 'rgba(56, 139, 253, 0.18)'
  const escala = (metrica - minimo) / (maximo - minimo) // 0 peor, 1 mejor
  return escala >= 0.5
    ? `rgba(63, 185, 80, ${0.1 + (escala - 0.5) * 0.7})`
    : `rgba(248, 81, 73, ${0.1 + (0.5 - escala) * 0.7})`
}

function ResultadosOptimizacion({ resultado, opciones }: Props) {
  const { resultados, mejor, validacion, sobreajuste, parametros } = resultado
  if (!mejor) return <p className="sin-resultados">Ninguna combinación llegó a operar.</p>

  const nombreDe = (indice: number) => {
    const param = parametros[indice]
    const opcion = opciones.find(
      (o) =>
        o.base.tipo === param.tipo &&
        o.base.campo === param.campo &&
        o.base.bloque === param.bloque &&
        o.base.indice === param.indice,
    )
    return opcion?.etiqueta ?? param.campo
  }

  const conMetrica = resultados.filter((r) => r.metrica !== null)
  const minimo = Math.min(...conMetrica.map((r) => r.metrica as number))
  const maximo = Math.max(...conMetrica.map((r) => r.metrica as number))

  const esMejor = (r: ResultadoCombinacion) =>
    r.valores.join(',') === mejor.valores.join(',')

  // Con dos parámetros se arma la matriz; con uno, una sola fila
  const dosParametros = parametros.length === 2
  const filas = [...new Set(resultados.map((r) => r.valores[0]))].sort((a, b) => a - b)
  const columnas = dosParametros
    ? [...new Set(resultados.map((r) => r.valores[1]))].sort((a, b) => a - b)
    : [null]

  const celda = (fila: number, columna: number | null) =>
    resultados.find(
      (r) => r.valores[0] === fila && (columna === null || r.valores[1] === columna),
    )

  return (
    <div className="resultados-optimizacion">
      <div className="mejor-combinacion">
        <div className="dato-mejor">
          <span className="etiqueta-mejor">Mejor combinación</span>
          <strong>
            {mejor.valores.map((valor, i) => `${nombreDe(i)} = ${valor}`).join(' · ')}
          </strong>
        </div>
        <div className="dato-mejor">
          <span className="etiqueta-mejor">Optimización (70% viejo)</span>
          <strong className={mejor.retorno_pct >= 0 ? 'positivo' : 'negativo'}>
            {pct(mejor.retorno_pct)}
          </strong>
          <span className="nota-mejor">{mejor.trades} ops</span>
        </div>
        {validacion && (
          <div className="dato-mejor">
            <span className="etiqueta-mejor">Validación (30% final)</span>
            <strong className={validacion.retorno_pct >= 0 ? 'positivo' : 'negativo'}>
              {pct(validacion.retorno_pct)}
            </strong>
            <span className="nota-mejor">{validacion.trades} ops · nunca lo vio</span>
          </div>
        )}
      </div>

      {sobreajuste.hay_sobreajuste ? (
        <div className="aviso-sobreajuste">
          <strong>⚠ Cuidado con el sobreajuste</strong>
          <ul>
            {sobreajuste.avisos.map((aviso, i) => (
              <li key={i}>{aviso}</li>
            ))}
          </ul>
        </div>
      ) : (
        <p className="sin-sobreajuste">
          ✓ Sin señales de sobreajuste: el resultado se sostiene fuera de la muestra.
        </p>
      )}

      <div className="heatmap-contenedor">
        <table className="heatmap-optimizacion">
          <thead>
            <tr>
              <th className="esquina">
                {nombreDe(0)}
                {dosParametros && ` \\ ${nombreDe(1)}`}
              </th>
              {columnas.map((columna, i) => (
                <th key={i}>{columna === null ? 'Resultado' : columna}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {filas.map((fila) => (
              <tr key={fila}>
                <th className="fila-encabezado">{fila}</th>
                {columnas.map((columna, i) => {
                  const dato = celda(fila, columna)
                  if (!dato) return <td key={i} className="celda-vacia">—</td>
                  return (
                    <td
                      key={i}
                      className={`celda-heatmap${esMejor(dato) ? ' mejor' : ''}`}
                      style={{ background: tonoCelda(dato.metrica, minimo, maximo) }}
                      title={`${pct(dato.retorno_pct)} · ${dato.trades} ops · DD ${dato.drawdown_pct.toFixed(1)}%`}
                    >
                      {num(dato.metrica)}
                    </td>
                  )
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <p className="leyenda-heatmap">
        Cada celda es la métrica optimizada; pasá el mouse para ver retorno, operaciones y drawdown.
        Buscá <strong>zonas</strong> buenas y no un valor aislado: si solo brilla una celda, es
        casualidad.
      </p>
    </div>
  )
}

export default ResultadosOptimizacion
