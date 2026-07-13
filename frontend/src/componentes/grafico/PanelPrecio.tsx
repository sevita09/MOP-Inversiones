import { forwardRef, useCallback, useEffect, useImperativeHandle, useMemo, useRef } from 'react'
import { createChart, PriceScaleMode } from 'lightweight-charts'
import type {
  CandlestickData,
  IChartApi,
  IPriceLine,
  ISeriesApi,
  LineData,
  MouseEventParams,
  SeriesType,
  Time,
  UTCTimestamp,
} from 'lightweight-charts'
import type {
  EscalaPrecio,
  Moneda,
  Temporalidad,
  TipoGrafico,
  Vela,
} from '../../api/tipos'
import { usarVelas } from '../../hooks/usarVelas'
import { usarBandas } from '../../hooks/usarBandas'
import { usarBollinger } from '../../hooks/usarBollinger'
import { usarNivelesSwing } from '../../hooks/usarNivelesSwing'
import { usarEstilos } from '../../contextos/EstilosContext'
import {
  usarEmasExtra,
  periodoExtraDe,
  tipoExtraDe,
  ANCHO_EXTRA_DEFAULT,
  TIPO_LINEA_EXTRA_DEFAULT,
} from '../../contextos/EmasExtraContext'
import { sincronizarEmasExtra, limpiarEmasExtra, type EmaCalculada } from './seriesEmasExtra'
import { mediaMovil } from './mediaMovil'
import { calcularVPVR } from './vpvr'
import { PrimitivaVPVR } from './primitivaVPVR'
import { REC_EMA, REC_BANDAS, REC_BOLLINGER } from './config/estilosIndicadores'
import { crearSeriesBollinger, volcarBollinger, aplicarEstiloBollinger } from './seriesBollinger'
import { dibujarNiveles, quitarNiveles } from './seriesNiveles'
import {
  MARGENES_VOLUMEN,
  OPCIONES_AREA,
  OPCIONES_GRAFICO,
  OPCIONES_LINEA,
  OPCIONES_VELAS,
  VOLUMEN_ROJO,
  VOLUMEN_VERDE,
} from './configGrafico'
import {
  crearSerieEma,
  crearSeriesBandas,
  volcarBandas,
  volcarEma,
  zEnIndice,
  aplicarEstiloEma,
  aplicarEstiloBandas,
} from './seriesBandas'
import type { SincronizadorTiempo } from './sincronizadorTiempo'
import LeyendaOHLC from './LeyendaOHLC'
import './PanelPrecio.css'

function datosVelas(velas: Vela[]): CandlestickData[] {
  return velas.map((vela) => ({
    time: vela.ts as UTCTimestamp,
    open: vela.apertura,
    high: vela.maximo,
    low: vela.minimo,
    close: vela.cierre,
  }))
}

function datosLinea(velas: Vela[]): LineData[] {
  return velas.map((vela) => ({ time: vela.ts as UTCTimestamp, value: vela.cierre }))
}

function crearSerie(chart: IChartApi, tipo: TipoGrafico): ISeriesApi<SeriesType> {
  if (tipo === 'linea') return chart.addLineSeries(OPCIONES_LINEA)
  if (tipo === 'area') return chart.addAreaSeries(OPCIONES_AREA)
  return chart.addCandlestickSeries(OPCIONES_VELAS)
}

function volcarDatos(serie: ISeriesApi<SeriesType>, tipo: TipoGrafico, velas: Vela[]) {
  serie.setData(tipo === 'velas' ? datosVelas(velas) : datosLinea(velas))
}

function datosVolumen(velas: Vela[]) {
  return velas.map((vela) => ({
    time: vela.ts as UTCTimestamp,
    value: vela.volumen,
    color: vela.cierre >= vela.apertura ? VOLUMEN_VERDE : VOLUMEN_ROJO,
  }))
}

// Valor de una serie de indicador en el índice del crosshair. Verifica que el ts
// coincida (velas e indicadores vienen del mismo query y alinean por índice).
function valorEnIndice(
  datos: { ts: number[]; series: Record<string, (number | null)[]> } | null,
  clave: string,
  indice: number,
  tsEsperado: number | undefined,
): number | null {
  if (!datos || tsEsperado == null || datos.ts[indice] !== tsEsperado) return null
  const arr = datos.series[clave]
  return arr ? arr[indice] ?? null : null
}

interface Props {
  ticker: string
  temporalidad: Temporalidad
  moneda: Moneda
  tipo: TipoGrafico
  escala: EscalaPrecio
  mostrarVolumen: boolean
  mostrarEma: boolean
  mostrarBandas: boolean
  mostrarBollinger: boolean
  mostrarNiveles: boolean
  mostrarVpvr: boolean
  sincronizador?: SincronizadorTiempo
  // Crosshair compartido: el ts bajo el mouse en cualquier panel, y cómo reportarlo
  tsActivo?: number | null
  alMoverCrosshair?: (ts: number | null) => void
}

export interface PanelPrecioHandle {
  verRango: (meses: number | null) => void
  obtenerChart: () => IChartApi | null
  obtenerSerie: () => ISeriesApi<SeriesType> | null
  // Imán: precio de la apertura o el cierre de la vela `ts`, el más cercano a `yPixel`
  precioIman: (ts: number, yPixel: number) => number | null
}

const DIAS_POR_MES = 30 * 86400

const PanelPrecio = forwardRef<PanelPrecioHandle, Props>(function PanelPrecio(
  {
    ticker,
    temporalidad,
    moneda,
    tipo,
    escala,
    mostrarVolumen,
    mostrarEma,
    mostrarBandas,
    mostrarBollinger,
    mostrarNiveles,
    mostrarVpvr,
    sincronizador,
    tsActivo = null,
    alMoverCrosshair,
  },
  ref,
) {
  const contenedor = useRef<HTMLDivElement>(null)
  const grafico = useRef<IChartApi | null>(null)
  const serie = useRef<ISeriesApi<SeriesType> | null>(null)
  const serieVolumen = useRef<ISeriesApi<'Histogram'> | null>(null)
  const serieEma = useRef<ISeriesApi<'Line'> | null>(null)
  const seriesBandas = useRef<Map<string, ISeriesApi<'Line'>> | null>(null)
  const seriesBollinger = useRef<Map<string, ISeriesApi<'Line'>> | null>(null)
  const seriesEmasExtra = useRef<Map<string, ISeriesApi<'Line'>>>(new Map())
  const vpvrPrim = useRef<PrimitivaVPVR | null>(null)
  const lineasNiveles = useRef<IPriceLine[]>([])
  const { velas, cargando, error } = usarVelas(ticker, temporalidad, moneda)
  // La media y las bandas salen del mismo indicador: basta con que alguno esté activo
  const bandas = usarBandas(ticker, temporalidad, moneda, mostrarEma || mostrarBandas)
  const bollinger = usarBollinger(ticker, temporalidad, moneda, mostrarBollinger)
  const bollingerRef = useRef(bollinger)
  bollingerRef.current = bollinger
  const niveles = usarNivelesSwing(ticker, temporalidad, moneda, mostrarNiveles)
  const bandasRef = useRef(bandas)
  bandasRef.current = bandas
  // El crosshair vive arriba (PaginaGrafico): reportamos el ts al moverlo
  const alMoverRef = useRef(alMoverCrosshair)
  alMoverRef.current = alMoverCrosshair

  // EMAs extra del usuario (se calculan en el frontend desde las velas)
  const { emas: emasExtra } = usarEmasExtra()

  // Estilo efectivo (recomendado + override del usuario) de los indicadores del panel
  const { estiloDe, paramsDe } = usarEstilos()
  // Multiplicador σ de la banda 1 (para recuperar σ y calcular el z correcto)
  const desvio1 = Number(paramsDe('bandas').desvio1 ?? 1) || 1
  const estEma = estiloDe('ema', REC_EMA)
  const estBandas = estiloDe('bandas', REC_BANDAS)
  const estBoll = estiloDe('bollinger', REC_BOLLINGER)
  const estEmaRef = useRef(estEma)
  estEmaRef.current = estEma
  const estBandasRef = useRef(estBandas)
  estBandasRef.current = estBandas
  const estBollRef = useRef(estBoll)
  estBollRef.current = estBoll

  const indicePorTs = useMemo(() => {
    const mapa = new Map<number, number>()
    velas.forEach((vela, indice) => mapa.set(vela.ts, indice))
    return mapa
  }, [velas])
  const velasRef = useRef(velas)
  velasRef.current = velas

  useImperativeHandle(ref, () => ({
    verRango(meses) {
      const chart = grafico.current
      if (!chart) return
      if (meses === null) {
        chart.timeScale().fitContent()
        return
      }
      const actuales = velasRef.current
      if (actuales.length === 0) return
      const hasta = actuales[actuales.length - 1].ts
      chart.timeScale().setVisibleRange({
        from: (hasta - meses * DIAS_POR_MES) as Time,
        to: hasta as Time,
      })
    },
    obtenerChart: () => grafico.current,
    obtenerSerie: () => serie.current,
    precioIman: (ts, yPixel) => {
      const s = serie.current
      const vela = velasRef.current.find((v) => v.ts === ts)
      if (!s || !vela) return null
      const yO = s.priceToCoordinate(vela.apertura)
      const yC = s.priceToCoordinate(vela.cierre)
      const dO = yO != null ? Math.abs(yO - yPixel) : Infinity
      const dC = yC != null ? Math.abs(yC - yPixel) : Infinity
      if (dO === Infinity && dC === Infinity) return null
      return dO <= dC ? vela.apertura : vela.cierre
    },
  }), [])

  // Crear el gráfico una sola vez; autoSize lo mantiene del tamaño del contenedor
  useEffect(() => {
    if (!contenedor.current) return
    const chart = createChart(contenedor.current, { ...OPCIONES_GRAFICO, autoSize: true })
    grafico.current = chart

    const alMover = (parametros: MouseEventParams) => {
      const ts = parametros.time as number | undefined
      alMoverRef.current?.(ts ?? null)
    }
    chart.subscribeCrosshairMove(alMover)
    const liberar = sincronizador?.registrar(chart)

    return () => {
      liberar?.()
      chart.unsubscribeCrosshairMove(alMover)
      chart.remove()
      grafico.current = null
      serie.current = null
      // El chart destruido se llevó sus series: el Map queda con refs muertas
      seriesEmasExtra.current.clear()
    }
  }, [sincronizador])

  // Aplicar la escala (lineal o logarítmica) al eje de precios
  useEffect(() => {
    grafico.current?.priceScale('right').applyOptions({
      mode: escala === 'log' ? PriceScaleMode.Logarithmic : PriceScaleMode.Normal,
    })
  }, [escala])

  // Crear/recrear la serie al cambiar el tipo de gráfico
  useEffect(() => {
    const chart = grafico.current
    if (!chart) return
    const s = crearSerie(chart, tipo)
    serie.current = s
    volcarDatos(s, tipo, velasRef.current)
    return () => {
      // Si el chart ya fue destruido, sus series se liberaron solas: ignorar
      try {
        chart.removeSeries(s)
      } catch {
        /* chart disposed */
      }
      serie.current = null
    }
  }, [tipo])

  // VPVR: perfil de volumen del rango visible, calculado en el frontend. Recalcula
  // el binning con las velas visibles y lo vuelca al primitivo (que redibuja).
  const recomputarVpvr = useCallback(() => {
    const chart = grafico.current
    const prim = vpvrPrim.current
    if (!chart || !prim) return
    const rango = chart.timeScale().getVisibleLogicalRange()
    const todas = velasRef.current
    if (!rango || todas.length === 0) {
      prim.setPerfil(null)
      return
    }
    const desde = Math.max(0, Math.floor(rango.from))
    const hasta = Math.min(todas.length, Math.ceil(rango.to) + 1)
    prim.setPerfil(calcularVPVR(todas.slice(desde, hasta)))
  }, [])

  // Crear/atachar el primitivo del VPVR con su toggle (y al recrearse la serie por
  // cambio de tipo). Recalcula al hacer pan/zoom (rango visible), con debounce.
  useEffect(() => {
    const chart = grafico.current
    const s = serie.current
    if (!chart || !s || !mostrarVpvr) return
    const prim = new PrimitivaVPVR(s)
    vpvrPrim.current = prim
    s.attachPrimitive(prim)
    recomputarVpvr()
    let temporizador: number | undefined
    const alCambiarRango = () => {
      if (temporizador) window.clearTimeout(temporizador)
      temporizador = window.setTimeout(recomputarVpvr, 120)
    }
    chart.timeScale().subscribeVisibleLogicalRangeChange(alCambiarRango)
    return () => {
      if (temporizador) window.clearTimeout(temporizador)
      chart.timeScale().unsubscribeVisibleLogicalRangeChange(alCambiarRango)
      try {
        s.detachPrimitive(prim)
        // detachPrimitive no repinta solo: un applyOptions vacío fuerza el redibujo
        // para que el histograma desaparezca ya, sin esperar a un pan/click.
        s.applyOptions({})
      } catch {
        /* serie disposed */
      }
      vpvrPrim.current = null
    }
  }, [mostrarVpvr, tipo, recomputarVpvr])

  // Recalcular el VPVR cuando cambian las velas (nueva data o refresco por sync)
  useEffect(() => {
    if (vpvrPrim.current) recomputarVpvr()
  }, [velas, recomputarVpvr])

  // Serie de volumen (histograma overlay anclado al fondo del panel)
  useEffect(() => {
    const chart = grafico.current
    if (!chart || !mostrarVolumen) return
    const v = chart.addHistogramSeries({
      priceFormat: { type: 'volume' },
      priceScaleId: '',
    })
    v.priceScale().applyOptions({ scaleMargins: MARGENES_VOLUMEN })
    v.setData(datosVolumen(velasRef.current))
    serieVolumen.current = v
    return () => {
      try {
        chart.removeSeries(v)
      } catch {
        /* chart disposed */
      }
      serieVolumen.current = null
    }
  }, [mostrarVolumen])

  // Línea de EMA central: se crea/elimina con su toggle
  useEffect(() => {
    const chart = grafico.current
    if (!chart || !mostrarEma) return
    const s = crearSerieEma(chart, estEmaRef.current)
    serieEma.current = s
    volcarEma(s, bandasRef.current)
    return () => {
      try {
        chart.removeSeries(s)
      } catch {
        /* chart disposed */
      }
      serieEma.current = null
    }
  }, [mostrarEma])

  // Bandas σ (las 6 líneas azules): se crean/eliminan con su toggle
  useEffect(() => {
    const chart = grafico.current
    if (!chart || !mostrarBandas) return
    const s = crearSeriesBandas(chart, estBandasRef.current)
    seriesBandas.current = s
    volcarBandas(s, bandasRef.current)
    return () => {
      for (const linea of s.values()) {
        try {
          chart.removeSeries(linea)
        } catch {
          /* chart disposed */
        }
      }
      seriesBandas.current = null
    }
  }, [mostrarBandas])

  // Bandas de Bollinger (3 líneas grises): se crean/eliminan con su toggle
  useEffect(() => {
    const chart = grafico.current
    if (!chart || !mostrarBollinger) return
    const s = crearSeriesBollinger(chart, estBollRef.current)
    seriesBollinger.current = s
    volcarBollinger(s, bollingerRef.current)
    return () => {
      for (const linea of s.values()) {
        try {
          chart.removeSeries(linea)
        } catch {
          /* chart disposed */
        }
      }
      seriesBollinger.current = null
    }
  }, [mostrarBollinger])

  // EMAs extra resueltas para la temporalidad actual (valores + estilo + rótulo).
  // Se calculan una vez y sirven para dibujar y para la leyenda del crosshair.
  const emasCalculadas = useMemo<EmaCalculada[]>(() => {
    const cierres = velas.map((v) => v.cierre)
    return emasExtra.map((ema) => {
      const periodo = periodoExtraDe(ema, temporalidad)
      const tipo = tipoExtraDe(ema, temporalidad)
      return {
        id: ema.id,
        etiqueta: `${tipo === 'simple' ? 'SMA' : 'EMA'} ${periodo}`,
        color: ema.color,
        ancho: ema.ancho ?? ANCHO_EXTRA_DEFAULT,
        tipoLinea: ema.tipoLinea ?? TIPO_LINEA_EXTRA_DEFAULT,
        valores: mediaMovil(cierres, periodo, tipo),
      }
    })
  }, [emasExtra, velas, temporalidad])

  // Dibujar las EMAs extra (comparten el toggle de la EMA central)
  useEffect(() => {
    const chart = grafico.current
    if (!chart) return
    if (mostrarEma) {
      sincronizarEmasExtra(chart, seriesEmasExtra.current, emasCalculadas, velas)
    } else {
      limpiarEmasExtra(chart, seriesEmasExtra.current)
    }
  }, [mostrarEma, emasCalculadas, velas])

  // Volcar los datos cuando cambian (ticker/temporalidad/moneda)
  useEffect(() => {
    if (serieEma.current) volcarEma(serieEma.current, bandas)
    if (seriesBandas.current) volcarBandas(seriesBandas.current, bandas)
  }, [bandas])

  useEffect(() => {
    if (seriesBollinger.current) volcarBollinger(seriesBollinger.current, bollinger)
  }, [bollinger])

  // Aplicar el estilo del usuario en vivo (doble click → cambia color/línea).
  // Se depende de los campos, no del objeto (estiloDe devuelve uno nuevo por render).
  useEffect(() => {
    if (serieEma.current) aplicarEstiloEma(serieEma.current, estEma)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [estEma.color, estEma.ancho, estEma.tipoLinea])

  useEffect(() => {
    if (seriesBandas.current) aplicarEstiloBandas(seriesBandas.current, estBandas)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [estBandas.color, estBandas.ancho, estBandas.tipoLinea])

  useEffect(() => {
    if (seriesBollinger.current) aplicarEstiloBollinger(seriesBollinger.current, estBoll)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [estBoll.color, estBoll.ancho, estBoll.tipoLinea])

  // Niveles S/R como líneas de precio sobre la serie principal. Se redibujan al
  // cambiar los datos o el tipo de gráfico (que recrea la serie). Sin cleanup:
  // cada corrida quita las anteriores; al recrearse la serie sus líneas se van
  // con ella (quitar las viejas es inocuo, va en try/catch).
  useEffect(() => {
    const s = serie.current
    if (!s) return
    quitarNiveles(s, lineasNiveles.current)
    lineasNiveles.current = mostrarNiveles && niveles ? dibujarNiveles(s, niveles) : []
  }, [niveles, mostrarNiveles, tipo])

  // Volcar las velas cuando cambian. El rango temporal solo se reencuadra al
  // cambiar de ticker o temporalidad, no al togglear moneda ni refrescar.
  const claveVista = `${ticker}-${temporalidad}`
  const claveAnterior = useRef('')
  useEffect(() => {
    if (serie.current) volcarDatos(serie.current, tipo, velas)
    serieVolumen.current?.setData(datosVolumen(velas))
    if (velas.length > 0 && claveAnterior.current !== claveVista) {
      grafico.current?.timeScale().fitContent()
      claveAnterior.current = claveVista
    }
  }, [velas, claveVista, tipo])

  // El índice bajo el crosshair sale del ts compartido; sin crosshair, la última vela
  const indiceActivo = tsActivo != null ? indicePorTs.get(tsActivo) ?? null : null
  const indiceMostrado = indiceActivo ?? velas.length - 1
  const velaMostrada = velas[indiceMostrado] ?? null
  const velaPrevia = indiceMostrado > 0 ? velas[indiceMostrado - 1] : null
  const hayVelas = velas.length > 0
  const sinDatos = !cargando && !error && !hayVelas
  const zBandas = zEnIndice(bandas, velaMostrada, indiceMostrado, desvio1)

  // Valores de EMA / bandas σ / Bollinger bajo el crosshair (solo si su toggle está)
  const tsMostrado = velaMostrada?.ts
  const emaValor = mostrarEma ? valorEnIndice(bandas, 'media', indiceMostrado, tsMostrado) : null
  const bandasValores = mostrarBandas
    ? {
        inf1: valorEnIndice(bandas, 'inf1', indiceMostrado, tsMostrado),
        sup1: valorEnIndice(bandas, 'sup1', indiceMostrado, tsMostrado),
        inf2: valorEnIndice(bandas, 'inf2', indiceMostrado, tsMostrado),
        sup2: valorEnIndice(bandas, 'sup2', indiceMostrado, tsMostrado),
        inf3: valorEnIndice(bandas, 'inf3', indiceMostrado, tsMostrado),
        sup3: valorEnIndice(bandas, 'sup3', indiceMostrado, tsMostrado),
      }
    : null
  const bollingerValores = mostrarBollinger
    ? {
        inferior: valorEnIndice(bollinger, 'inferior', indiceMostrado, tsMostrado),
        media: valorEnIndice(bollinger, 'media', indiceMostrado, tsMostrado),
        superior: valorEnIndice(bollinger, 'superior', indiceMostrado, tsMostrado),
      }
    : null
  // Valor de cada EMA extra bajo el crosshair (comparten el toggle de la EMA central)
  const emasExtraValores = mostrarEma
    ? emasCalculadas.map((e) => ({
        id: e.id,
        etiqueta: e.etiqueta,
        color: e.color,
        valor: e.valores[indiceMostrado] ?? null,
      }))
    : []

  return (
    <div className="panel-precio">
      {velaMostrada && (
        <LeyendaOHLC
          vela={velaMostrada}
          velaPrevia={velaPrevia}
          z={zBandas}
          ema={emaValor}
          bandas={bandasValores}
          bollinger={bollingerValores}
          emasExtra={emasExtraValores}
        />
      )}
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
        <div className="grafico-banner-error">Sin conexión — mostrando datos previos</div>
      )}
      {sinDatos && (
        <div className="grafico-estado">Sin datos para {ticker} en {temporalidad}</div>
      )}
    </div>
  )
})

export default PanelPrecio
