import { useEffect, useMemo, useState } from 'react'
import type { Moneda, TemporalidadBot } from '../../api/tipos'
import MapaCalor from '../../componentes/comunes/MapaCalor'
import SelectorPapeles from '../../componentes/analisis/SelectorPapeles'
import { usarMatrizCorrelacion, usarPapelesDeCartera } from '../../hooks/usarCorrelaciones'
import { PERIODOS, desdeTs } from './periodos'
import './PaginaCorrelaciones.css'

// Si todavía no hay cartera, algo con qué mirar el panel local
const SUGERIDOS = ['GGAL', 'BMA', 'YPFD', 'PAMP', 'ALUA', 'TGSU2']

const coeficiente = (valor: number) => valor.toFixed(2)

function PaginaCorrelaciones() {
  const deCartera = usarPapelesDeCartera()
  const [papeles, setPapeles] = useState<string[]>([])
  const [temporalidad, setTemporalidad] = useState<TemporalidadBot>('D')
  const [moneda, setMoneda] = useState<Moneda>('USD')
  const [periodo, setPeriodo] = useState('5Y')

  // Arranca con lo que hay en cartera; si no hay, con el panel local
  useEffect(() => {
    if (deCartera === null) return
    setPapeles(deCartera.length >= 2 ? deCartera : SUGERIDOS)
  }, [deCartera])

  // El período recorta el tramo de historia sobre el que se mide la matriz
  const meses = PERIODOS.find((p) => p.clave === periodo)?.meses ?? 60
  const desde = useMemo(() => desdeTs(meses), [meses])

  const { matriz, cargando } = usarMatrizCorrelacion(papeles, temporalidad, moneda, desde)

  return (
    <div className="pagina-correlaciones">
      <div className="cabecera-correlaciones">
        <h2>Correlaciones</h2>
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

      <SelectorPapeles elegidos={papeles} alCambiar={setPapeles} temporalidad={temporalidad} />

      {papeles.length < 2 && (
        <p className="correlaciones-vacio">Elegí al menos dos papeles para comparar.</p>
      )}
      {cargando && <p className="correlaciones-vacio">Calculando…</p>}

      {matriz && !cargando && (
        <>
          <MapaCalor
            columnas={matriz.tickers}
            filas={matriz.tickers}
            valores={matriz.matriz}
            extremo={1}
            formato={coeficiente}
            descripcion={(fila, columna, valor) =>
              `${fila} vs ${columna}: ${coeficiente(valor)}`
            }
          />
          <p className="nota-correlaciones">
            Sobre <strong>retornos</strong>, nunca sobre precios: dos series con tendencia dan
            correlación alta aunque no tengan nada que ver. Solo cuentan las ruedas donde operaron
            los dos papeles, y por debajo de {matriz.minimo} en común la celda queda vacía — con
            períodos cortos o temporalidad mensual eso pasa seguido.
            {moneda === 'ARS' && (
              <>
                {' '}
                <strong>En pesos la devaluación es un factor común</strong> que empuja todas las
                correlaciones: para ver si dos posiciones son en realidad una sola, mirá en dólares.
              </>
            )}
          </p>

        </>
      )}
    </div>
  )
}

export default PaginaCorrelaciones
