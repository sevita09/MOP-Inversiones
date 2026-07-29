import { useEffect, useRef, useState } from 'react'
import { createChart } from 'lightweight-charts'
import type { IChartApi, ISeriesApi, LineData, UTCTimestamp } from 'lightweight-charts'
import type { Moneda, Rendimiento } from '../../api/tipos'
import { COLORES, OPCIONES_GRAFICO } from '../grafico/configGrafico'
import { PERIODOS } from '../../hooks/usarRendimiento'
import './CurvaRendimiento.css'

interface Props {
  datos: Rendimiento
  periodo: string
  alCambiarPeriodo: (periodo: string) => void
  moneda: Moneda
  alCambiarMoneda: (moneda: Moneda) => void
}

/** Un color por serie. Los tres dólares son tonos del mismo dorado: se leen
 *  como familia y se distinguen entre sí. */
const COLORES_SERIE: Record<string, string> = {
  cartera: COLORES.azul,
  mercado: '#8b949e',
  inflacion: '#a371f7',
  brkb: '#f778ba',
  spy: '#3fb950',
  qqq: '#39c5cf',
  btc: '#f7931a',
  oficial: '#bb8009',
  mep: '#d29922',
  dolar: '#e3b341',
}

/** Orden de lectura de la grilla: fila por fila, tres columnas.
 *  La tercera de la primera columna cambia según la moneda. */
const FILAS = [
  ['cartera', 'spy', 'oficial'],
  ['mercado', 'qqq', 'mep'],
  ['inflacion', 'btc', 'dolar'],
]

const NOMBRES: Record<string, string> = {
  cartera: 'Mi cartera',
  mercado: 'MERVAL',
  inflacion: 'Inflación',
  brkb: 'BRK.B',
  spy: 'S&P',
  qqq: 'QQQ',
  btc: 'BTC',
  oficial: 'Dólar oficial',
  mep: 'Dólar MEP',
  dolar: 'Dólar CCL',
}

/** Los tres dólares se nombran solos; el resto lleva la moneda en que se mide. */
const SIN_MONEDA = ['oficial', 'mep', 'dolar']

/** Valor de cada serie bajo el crosshair; vacío cuando el mouse está afuera. */
type Valores = Record<string, number | undefined>

/** 'AAAA-MM-DD' a ts UTC, el formato que entiende el chart. */
function aLinea(fechas: string[], valores: (number | null)[] | undefined): LineData[] {
  const puntos: LineData[] = []
  if (!valores) return puntos
  fechas.forEach((fecha, indice) => {
    const valor = valores[indice]
    if (valor === null || valor === undefined) return
    puntos.push({ time: (Date.parse(`${fecha}T00:00:00Z`) / 1000) as UTCTimestamp, value: valor })
  })
  return puntos
}

/** Base 100 a variación: 122,27 se lee "+22,3%". */
function comoPorcentaje(valor: number | undefined): string {
  if (valor === undefined) return ''
  const variacion = valor - 100
  const signo = variacion > 0 ? '+' : ''
  return `${signo}${variacion.toFixed(1).replace('.', ',')}%`
}

/** Cartera, dólares, MERVAL e inflación en base 100 desde la primera rueda. */
function CurvaRendimiento({ datos, periodo, alCambiarPeriodo, moneda, alCambiarMoneda }: Props) {
  const contenedor = useRef<HTMLDivElement>(null)
  const chartRef = useRef<IChartApi | null>(null)
  const series = useRef<Record<string, ISeriesApi<'Line'> | null>>({})
  const [valores, setValores] = useState<Valores>({})

  useEffect(() => {
    if (!contenedor.current) return
    const chart = createChart(contenedor.current, {
      ...OPCIONES_GRAFICO,
      autoSize: true,
      timeScale: { ...OPCIONES_GRAFICO.timeScale, timeVisible: false },
    })
    chartRef.current = chart

    // Los benchmarks van primero (debajo) y punteados: son la referencia.
    // La cartera va última y llena, para que quede encima de todas.
    const referencia = {
      lineWidth: 1 as const,
      lineStyle: 2,
      priceLineVisible: false,
      lastValueVisible: false,
    }
    for (const clave of Object.keys(COLORES_SERIE)) {
      if (clave === 'cartera') continue
      series.current[clave] = chart.addLineSeries({
        ...referencia,
        color: COLORES_SERIE[clave],
      })
    }
    series.current.cartera = chart.addLineSeries({
      color: COLORES_SERIE.cartera,
      lineWidth: 2,
      priceLineVisible: false,
    })

    // El valor de cada serie bajo el mouse se muestra en la leyenda
    chart.subscribeCrosshairMove((parametros) => {
      if (parametros.time === undefined || !parametros.point) {
        setValores({})
        return
      }
      const leidos: Valores = {}
      for (const [nombre, serie] of Object.entries(series.current)) {
        if (!serie) continue
        leidos[nombre] = (parametros.seriesData.get(serie) as LineData | undefined)?.value
      }
      setValores(leidos)
    })

    return () => {
      chartRef.current = null
      series.current = {}
      chart.remove()
    }
  }, [])

  useEffect(() => {
    if (!series.current.cartera) return
    series.current.cartera.setData(aLinea(datos.fechas, datos.cartera))
    for (const clave of Object.keys(COLORES_SERIE)) {
      if (clave === 'cartera') continue
      const serie = series.current[clave]
      // Las que no vienen en esta moneda (inflación en USD, BRK.B en ARS)
      // quedan vacías: la serie existe pero no dibuja nada
      serie?.setData(aLinea(datos.fechas, datos.benchmarks[clave as keyof typeof datos.benchmarks]))
    }
    setValores({})
    chartRef.current?.timeScale().fitContent()
  }, [datos])

  /** La grilla se arma con las series que existen en esta moneda. */
  const filas = FILAS.map((fila) =>
    fila.map((clave) => {
      if (clave === 'inflacion' && !datos.benchmarks.inflacion) return 'brkb'
      return clave
    }),
  )

  return (
    <div className="curva-rendimiento">
      <div className="encabezado-curva">
        <div className="leyenda-rendimiento">
          {filas.flat().map((clave) => (
            <span key={clave} className={`serie-rendimiento ${clave}`}>
              <span className="trazo-serie">{clave === 'cartera' ? '━' : '╌'}</span>
              {NOMBRES[clave]}
              {!SIN_MONEDA.includes(clave) && ` ${moneda}`}
              <span className="valor-serie">{comoPorcentaje(valores[clave])}</span>
            </span>
          ))}
        </div>
        <div className="controles-curva">
          <div className="monedas-rendimiento">
            {(['ARS', 'USD'] as Moneda[]).map((opcion) => (
              <button
                key={opcion}
                type="button"
                className={moneda === opcion ? 'moneda-rendimiento activa' : 'moneda-rendimiento'}
                onClick={() => alCambiarMoneda(opcion)}
              >
                {opcion === 'ARS' ? 'Pesos' : 'Dólares'}
              </button>
            ))}
          </div>
          <div className="periodos-rendimiento">
            {PERIODOS.map(({ clave }) => (
              <button
                key={clave}
                type="button"
                className={periodo === clave ? 'periodo-rendimiento activo' : 'periodo-rendimiento'}
                onClick={() => alCambiarPeriodo(clave)}
              >
                {clave}
              </button>
            ))}
          </div>
        </div>
      </div>
      <div ref={contenedor} className="area-rendimiento" />
      <span className="nota-rendimiento">base 100 {moneda}</span>
    </div>
  )
}

export default CurvaRendimiento
