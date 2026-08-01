import { useMemo, useState } from 'react'
import type { Moneda, TemporalidadBot } from '../../api/tipos'
import CorrelacionRolling from '../../componentes/analisis/CorrelacionRolling'
import Dispersion from '../../componentes/analisis/Dispersion'
import SelectorSerie from '../../componentes/analisis/SelectorSerie'
import { usarCorrelacionPar } from '../../hooks/usarCorrelaciones'
import {
  BARRAS_POR_MES,
  FRACCION_VENTANA,
  MUESTRA_CONFIABLE,
  PERIODOS,
  VENTANA_MINIMA,
  desdeTs,
} from './periodos'
import './PaginaCorrelaciones.css'

/** El ratio de un par: cómo cambió su correlación en el tiempo y la nube de
 *  retornos que hay detrás del número. */
function PaginaRatios() {
  const [a, setA] = useState('GGAL')
  const [b, setB] = useState('MERVAL')
  const [temporalidad, setTemporalidad] = useState<TemporalidadBot>('D')
  const [moneda, setMoneda] = useState<Moneda>('USD')
  const [periodo, setPeriodo] = useState('5Y')

  const meses = PERIODOS.find((p) => p.clave === periodo)?.meses ?? 60
  const desde = useMemo(() => desdeTs(meses), [meses])
  const barras = Math.round(meses * BARRAS_POR_MES[temporalidad])
  const ventana = Math.max(VENTANA_MINIMA, Math.round(barras / FRACCION_VENTANA))

  const detalle = usarCorrelacionPar(a || null, b || null, temporalidad, moneda, ventana, desde)
  const unidad = temporalidad === 'D' ? 'ruedas' : temporalidad === 'S' ? 'semanas' : 'meses'

  return (
    <div className="pagina-correlaciones">
      <div className="cabecera-correlaciones">
        <h2>Ratio</h2>
        <div className="controles-correlaciones">
          <div className="grupo-control">
            {PERIODOS.map(({ clave }) => (
              <button
                key={clave}
                type="button"
                className={periodo === clave ? 'control-corr activo' : 'control-corr'}
                onClick={() => setPeriodo(clave)}
              >
                {clave}
              </button>
            ))}
          </div>
          <div className="grupo-control">
            {(['D', 'S', 'M'] as TemporalidadBot[]).map((opcion) => (
              <button
                key={opcion}
                type="button"
                className={temporalidad === opcion ? 'control-corr activo' : 'control-corr'}
                onClick={() => setTemporalidad(opcion)}
              >
                {opcion}
              </button>
            ))}
          </div>
          <div className="grupo-control">
            {(['ARS', 'USD'] as Moneda[]).map((opcion) => (
              <button
                key={opcion}
                type="button"
                className={moneda === opcion ? 'control-corr activo' : 'control-corr'}
                onClick={() => setMoneda(opcion)}
              >
                {opcion === 'ARS' ? 'Pesos' : 'Dólares'}
              </button>
            ))}
          </div>
        </div>
      </div>

      <div className="controles-par">
        <label>
          Par
          <SelectorSerie valor={a} alCambiar={setA} temporalidad={temporalidad} etiqueta="Serie A" />
          <span className="contra">vs</span>
          <SelectorSerie valor={b} alCambiar={setB} temporalidad={temporalidad} etiqueta="Serie B" />
        </label>
        <span className="ventana-info">
          {periodo} de historia · ventana móvil de {ventana} {unidad}
          {ventana < MUESTRA_CONFIABLE && (
            <strong className="aviso-muestra"> · muestra chica, tomalo con pinzas</strong>
          )}
        </span>
      </div>

      {a && b && a === b && (
        <p className="correlaciones-vacio">Elegí dos series distintas.</p>
      )}

      {detalle && detalle.puntos.length > 0 ? (
        <>
          <div className="detalle-par">
            <CorrelacionRolling
              puntos={detalle.puntos}
              ventana={detalle.ventana}
              total={detalle.correlacion_total}
            />
            <Dispersion
              puntos={detalle.dispersion}
              a={detalle.a}
              b={detalle.b}
              correlacion={detalle.correlacion_ventana}
              periodo={periodo}
            />
          </div>
          <p className="nota-correlaciones">
            La línea es la correlación calculada sobre una ventana móvil de {ventana} {unidad}:
            un coeficiente único sobre años esconde lo que importa, porque dos papeles pueden
            estar descorrelacionados mucho tiempo y pegarse en una crisis —justo cuando la
            diversificación tendría que servir—. La nube son los retornos de las {' '}
            {detalle.dispersion.length.toLocaleString('es-AR')} ruedas del período: muestra si la
            relación es pareja o la arman cuatro días extremos.
          </p>
        </>
      ) : (
        <p className="correlaciones-vacio">
          {detalle
            ? `Hay ${detalle.pares} datos en común: menos que la ventana de ${ventana}. Achicá el período o pasá a una temporalidad más corta.`
            : 'Elegí dos series para ver cómo cambió su relación en el tiempo.'}
        </p>
      )}
    </div>
  )
}

export default PaginaRatios
