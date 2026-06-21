import type {
  IChartApi,
  ISeriesApi,
  ISeriesPrimitive,
  ISeriesPrimitivePaneRenderer,
  ISeriesPrimitivePaneView,
  SeriesAttachedParameter,
  SeriesType,
  Time,
} from 'lightweight-charts'
import type { CanvasRenderingTarget2D } from 'fancy-canvas'

const VERDE = '#3fb950'
const ROJO = '#f85149'
const RELLENO_VERDE = 'rgba(63, 185, 80, 0.12)'
const RELLENO_ROJO = 'rgba(248, 81, 73, 0.12)'
const FONDO_ETIQUETA = '#0d1117'

interface Punto {
  ts: number
  precio: number
}

interface Pixel {
  x: number
  y: number
}

class RendererMedicion implements ISeriesPrimitivePaneRenderer {
  private _x1 = 0
  private _y1 = 0
  private _x2 = 0
  private _y2 = 0
  private _texto = ''
  private _sube = true
  private _punteada: boolean
  private _seleccionado = false

  constructor(punteada: boolean) {
    this._punteada = punteada
  }

  actualizar(x1: number, y1: number, x2: number, y2: number, texto: string, sube: boolean) {
    this._x1 = x1
    this._y1 = y1
    this._x2 = x2
    this._y2 = y2
    this._texto = texto
    this._sube = sube
  }

  seleccionar(sel: boolean) {
    this._seleccionado = sel
  }

  draw(target: CanvasRenderingTarget2D) {
    target.useMediaCoordinateSpace(({ context: ctx }) => {
      const izq = Math.min(this._x1, this._x2)
      const der = Math.max(this._x1, this._x2)
      const arr = Math.min(this._y1, this._y2)
      const aba = Math.max(this._y1, this._y2)
      const color = this._sube ? VERDE : ROJO

      ctx.fillStyle = this._sube ? RELLENO_VERDE : RELLENO_ROJO
      ctx.fillRect(izq, arr, der - izq, aba - arr)

      ctx.strokeStyle = color
      ctx.lineWidth = this._seleccionado ? 2 : 1
      ctx.setLineDash(this._punteada ? [4, 4] : [])
      ctx.strokeRect(izq, arr, der - izq, aba - arr)
      ctx.setLineDash([])

      ctx.font = '11px sans-serif'
      ctx.textAlign = 'center'
      ctx.textBaseline = 'middle'
      const cx = (izq + der) / 2
      const cy = this._sube ? arr - 10 : aba + 10
      const ancho = ctx.measureText(this._texto).width + 10
      ctx.fillStyle = color
      ctx.fillRect(cx - ancho / 2, cy - 9, ancho, 18)
      ctx.fillStyle = FONDO_ETIQUETA
      ctx.fillText(this._texto, cx, cy)
      ctx.textAlign = 'left'
    })
  }
}

class VistaMedicion implements ISeriesPrimitivePaneView {
  private _renderer: RendererMedicion
  private _serie: ISeriesApi<SeriesType>
  private _chart: IChartApi
  p1: Punto
  p2: Punto
  p2pixel: Pixel | null = null

  constructor(
    chart: IChartApi,
    serie: ISeriesApi<SeriesType>,
    p1: Punto,
    p2: Punto,
    punteada: boolean,
  ) {
    this._chart = chart
    this._serie = serie
    this.p1 = p1
    this.p2 = p2
    this._renderer = new RendererMedicion(punteada)
  }

  update() {
    const ts = this._chart.timeScale()
    const x1 = ts.timeToCoordinate(this.p1.ts as unknown as Time)
    const y1 = this._serie.priceToCoordinate(this.p1.precio)
    if (x1 == null || y1 == null) return

    let x2: number | null
    let y2: number | null
    let precio2: number
    if (this.p2pixel) {
      x2 = this.p2pixel.x
      y2 = this.p2pixel.y
      const pr = this._serie.coordinateToPrice(this.p2pixel.y)
      if (pr == null) return
      precio2 = pr
    } else {
      x2 = ts.timeToCoordinate(this.p2.ts as unknown as Time)
      y2 = this._serie.priceToCoordinate(this.p2.precio)
      precio2 = this.p2.precio
    }
    if (x2 == null || y2 == null) return

    const pct = this.p1.precio !== 0 ? ((precio2 - this.p1.precio) / this.p1.precio) * 100 : 0
    const l1 = ts.coordinateToLogical(x1)
    const l2 = ts.coordinateToLogical(x2)
    const barras = l1 != null && l2 != null ? Math.abs(Math.round(l2 - l1)) : 0
    const signo = pct >= 0 ? '+' : ''
    const texto = `${signo}${pct.toFixed(2)}%   ${barras} barras`
    this._renderer.actualizar(x1, y1, x2, y2, texto, precio2 >= this.p1.precio)
  }

  seleccionar(sel: boolean) {
    this._renderer.seleccionar(sel)
  }

  renderer() {
    return this._renderer
  }

  zOrder(): 'top' {
    return 'top'
  }
}

export class PrimitivaMedicion implements ISeriesPrimitive {
  private _vista: VistaMedicion
  private _requestUpdate?: () => void

  constructor(
    chart: IChartApi,
    serie: ISeriesApi<SeriesType>,
    p1: Punto,
    p2: Punto,
    punteada = false,
  ) {
    this._vista = new VistaMedicion(chart, serie, p1, p2, punteada)
  }

  attached(param: SeriesAttachedParameter<Time>) {
    this._requestUpdate = param.requestUpdate
  }

  detached() {
    this._requestUpdate = undefined
  }

  paneViews() {
    return [this._vista]
  }

  updateAllViews() {
    this._vista.update()
  }

  actualizar(p1: Punto, p2: Punto) {
    this._vista.p1 = p1
    this._vista.p2 = p2
    this._vista.p2pixel = null
    this._requestUpdate?.()
  }

  actualizarPixel(x: number, y: number) {
    this._vista.p2pixel = { x, y }
    this._requestUpdate?.()
  }

  seleccionar(sel: boolean) {
    this._vista.seleccionar(sel)
    this._requestUpdate?.()
  }
}
