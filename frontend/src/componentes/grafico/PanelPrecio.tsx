import { useEffect, useMemo, useRef, useState } from 'react'
import { createChart } from 'lightweight-charts'
import type {
  CandlestickData,
  IChartApi,
  ISeriesApi,
  MouseEventParams,
  UTCTimestamp,
} from 'lightweight-charts'
import type { Moneda, Temporalidad, Vela } from '../../api/tipos'
import { usarVelas } from '../../hooks/usarVelas'
import { OPCIONES_GRAFICO, OPCIONES_VELAS } from './configGrafico'
import LeyendaOHLC from './LeyendaOHLC'

function aDatosVelas(velas: Vela[]): CandlestickData[] {
  return velas.map((vela) => ({
    time: vela.ts as UTCTimestamp,
    open: vela.apertura,
    high: vela.maximo,
    low: vela.minimo,
    close: vela.cierre,
  }))
}

interface Props {
  ticker: string
  temporalidad: Temporalidad
  moneda: Moneda
}

function PanelPrecio({ ticker, temporalidad, moneda }: Props) {
  const contenedor = useRef<HTMLDivElement>(null)
  const grafico = useRef<IChartApi | null>(null)
  const serie = useRef<ISeriesApi<'Candlestick'> | null>(null)
  const { velas, cargando, error } = usarVelas(ticker, temporalidad, moneda)
  // Índice de la vela bajo el crosshair; null = ninguna (se muestra la última)
  const [indiceActivo, setIndiceActivo] = useState<number | null>(null)

  const indicePorTs = useMemo(() => {
    const mapa = new Map<number, number>()
    velas.forEach((vela, indice) => mapa.set(vela.ts, indice))
    return mapa
  }, [velas])
  // El handler del crosshair se crea una sola vez; el ref le da siempre el mapa actual
  const indicePorTsRef = useRef(indicePorTs)
  indicePorTsRef.current = indicePorTs

  // Crear el gráfico una sola vez; autoSize lo mantiene del tamaño del contenedor
  useEffect(() => {
    if (!contenedor.current) return
    const chart = createChart(contenedor.current, {
      ...OPCIONES_GRAFICO,
      autoSize: true,
    })
    serie.current = chart.addCandlestickSeries(OPCIONES_VELAS)
    grafico.current = chart

    const alMover = (parametros: MouseEventParams) => {
      const ts = parametros.time as number | undefined
      setIndiceActivo(ts != null ? indicePorTsRef.current.get(ts) ?? null : null)
    }
    chart.subscribeCrosshairMove(alMover)

    return () => {
      chart.unsubscribeCrosshairMove(alMover)
      chart.remove()
      grafico.current = null
      serie.current = null
    }
  }, [])

  // Volcar las velas cuando cambian. El precio autoescala solo (autoScale por
  // defecto); el rango temporal solo se reencuadra al cambiar de ticker o
  // temporalidad, no al togglear moneda ni al refrescar el mismo papel —
  // así no se pierde el zoom o el desplazamiento del usuario.
  const claveVista = `${ticker}-${temporalidad}`
  const claveAnterior = useRef('')
  useEffect(() => {
    if (!serie.current) return
    serie.current.setData(aDatosVelas(velas))
    if (velas.length > 0 && claveAnterior.current !== claveVista) {
      grafico.current?.timeScale().fitContent()
      claveAnterior.current = claveVista
    }
  }, [velas, claveVista])

  const indiceMostrado = indiceActivo ?? velas.length - 1
  const velaMostrada = velas[indiceMostrado] ?? null
  const velaPrevia = indiceMostrado > 0 ? velas[indiceMostrado - 1] : null
  const hayVelas = velas.length > 0
  const sinDatos = !cargando && !error && !hayVelas

  return (
    <div className="panel-precio">
      {velaMostrada && <LeyendaOHLC vela={velaMostrada} velaPrevia={velaPrevia} />}
      <div ref={contenedor} className="grafico" />
      {cargando && !hayVelas && (
        <div className="grafico-estado">
          <span className="spinner" />
          Cargando {ticker}…
        </div>
      )}
      {error && !hayVelas && (
        <div className="grafico-estado grafico-estado-error">
          No se pudieron cargar los datos
          <span className="grafico-estado-detalle">{error}</span>
        </div>
      )}
      {error && hayVelas && (
        // Ya hay datos en pantalla: el error va como aviso discreto, sin tapar el gráfico
        <div className="grafico-banner-error">Sin conexión — mostrando datos previos</div>
      )}
      {sinDatos && (
        <div className="grafico-estado">Sin datos para {ticker} en {temporalidad}</div>
      )}
    </div>
  )
}

export default PanelPrecio
