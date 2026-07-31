import { useEffect, useState } from 'react'
import { obtenerEstacionalidad } from '../../api/cliente'
import type { Estacionalidad, Moneda, VistaEstacional } from '../../api/tipos'
import LogoTicker from '../../componentes/LogoTicker'
import MapaCalor from '../../componentes/comunes/MapaCalor'
import type { FilaResumen } from '../../componentes/comunes/MapaCalor'
import { usarTicker } from '../../contextos/TickerContext'
import './PaginaEstacionalidad.css'

const porcentaje = (valor: number) => `${valor > 0 ? '+' : ''}${valor.toFixed(1)}`
const proporcion = (valor: number) => `${valor.toFixed(0)}%`

// Dónde satura el color de cada vista: un mes de ±15% ya es un mes fuerte,
// mientras que un día promedio de ±0,5% es muchísimo
const EXTREMO = { mes: 15, dia_semana: 0.5 }

function PaginaEstacionalidad() {
  const { ticker } = usarTicker()
  const [moneda, setMoneda] = useState<Moneda>('USD')
  const [vista, setVista] = useState<VistaEstacional>('mes')
  const [datos, setDatos] = useState<Estacionalidad | null>(null)
  const [cargando, setCargando] = useState(true)

  useEffect(() => {
    let vigente = true
    setCargando(true)
    obtenerEstacionalidad(ticker, moneda, vista)
      .then((respuesta) => vigente && setDatos(respuesta))
      .catch(() => vigente && setDatos(null))
      .finally(() => vigente && setCargando(false))
    return () => {
      vigente = false
    }
  }, [ticker, moneda, vista])

  const resumen: FilaResumen[] = datos
    ? [
        { etiqueta: 'promedio', valores: datos.resumen.map((r) => r.promedio_pct) },
        { etiqueta: 'mediana', valores: datos.resumen.map((r) => r.mediana_pct) },
        {
          etiqueta: 'positivos',
          valores: datos.resumen.map((r) => r.positivos_pct),
          formato: proporcion,
          // Acá el umbral es la mitad: menos del 50% de años positivos es malo
          centro: 50,
        },
      ]
    : []

  return (
    <div className="pagina-estacionalidad">
      <div className="cabecera-estacionalidad">
        <h2>
          <LogoTicker ticker={ticker} tamano={22} />
          Estacionalidad de {ticker}
        </h2>
        <div className="controles-estacionalidad">
          <div className="grupo-control">
            {(['mes', 'dia_semana'] as VistaEstacional[]).map((opcion) => (
              <button
                key={opcion}
                type="button"
                className={vista === opcion ? 'control-estacional activo' : 'control-estacional'}
                onClick={() => setVista(opcion)}
              >
                {opcion === 'mes' ? 'Por mes' : 'Por día'}
              </button>
            ))}
          </div>
          <div className="grupo-control">
            {(['ARS', 'USD'] as Moneda[]).map((opcion) => (
              <button
                key={opcion}
                type="button"
                className={moneda === opcion ? 'control-estacional activo' : 'control-estacional'}
                onClick={() => setMoneda(opcion)}
              >
                {opcion === 'ARS' ? 'Pesos' : 'Dólares'}
              </button>
            ))}
          </div>
        </div>
      </div>

      {cargando && <p className="estacionalidad-cargando">Armando el cuadro…</p>}

      {!cargando && (!datos || datos.anios.length === 0) && (
        <p className="estacionalidad-vacia">
          Todavía no hay historia suficiente de {ticker} para este cuadro.
        </p>
      )}

      {!cargando && datos && datos.anios.length > 0 && (
        <>
          <MapaCalor
            columnas={datos.columnas}
            filas={datos.anios}
            valores={datos.matriz}
            extremo={EXTREMO[vista]}
            formato={porcentaje}
            totales={vista === 'mes' ? datos.totales_anio : undefined}
            tituloTotales="Año"
            resumen={resumen}
            descripcion={(anio, columna, valor) =>
              `${columna} ${anio}: ${porcentaje(valor)}% · ${datos.detalle}`
            }
          />

          <p className="nota-estacionalidad">
            Cada celda es el <strong>{datos.detalle}</strong> en {moneda}, y el color solo
            refuerza lo que dice el número. Abajo, sobre todos los años: el promedio (encadenado,
            no la suma de porcentajes), la mediana y qué proporción de las veces fue positivo.
            {moneda === 'ARS' && (
              <>
                {' '}
                <strong>En pesos la inflación pinta de verde casi todo</strong>: para leer
                estacionalidad de verdad, mirá el cuadro en dólares.
              </>
            )}
          </p>
        </>
      )}
    </div>
  )
}

export default PaginaEstacionalidad
