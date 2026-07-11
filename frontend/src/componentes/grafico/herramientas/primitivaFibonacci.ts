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
import { RECOMENDADO_DIBUJO, dashDe, type EstiloDibujo } from './estiloDibujo'

export const NIVELES_FIBONACCI = [0, 0.236, 0.382, 0.5, 0.618, 0.786, 1]
const COLOR_SELECCION = '#ffffff'
const COLOR_TEXTO = '#e6edf3'

interface Punto {
  ts: number
  precio: number
}

interface Pixel {
  x: number
  y: number
}

interface NivelDibujo {
  y: number
  etiqueta: string
}

class RendererFibonacci implements ISeriesPrimitivePaneRenderer {
  private _x1 = 0
  private _x2 = 0
  private _niveles: NivelDibujo[] = []
  private _punteada: boolean
  private _estilo: EstiloDibujo
  private _seleccionado = false

  constructor(estilo: EstiloDibujo, punteada: boolean) {
    this._estilo = estilo
    this._punteada = punteada
  }

  actualizar(x1: number, x2: number, niveles: NivelDibujo[]) {
    this._x1 = x1
    this._x2 = x2
    this._niveles = niveles
  }

  setEstilo(estilo: EstiloDibujo) {
    this._estilo = estilo
  }

  seleccionar(sel: boolean) {
    this._seleccionado = sel
  }

  draw(target: CanvasRenderingTarget2D) {
    target.useMediaCoordinateSpace(({ context: ctx }) => {
      const izq = Math.min(this._x1, this._x2)
      const der = Math.max(this._x1, this._x2)
      const ancho = this._estilo.ancho ?? 1
      ctx.lineWidth = this._seleccionado ? ancho + 1 : ancho
      ctx.strokeStyle = this._seleccionado ? COLOR_SELECCION : this._estilo.color ?? RECOMENDADO_DIBUJO.color!
      ctx.fillStyle = COLOR_TEXTO
      ctx.font = '11px sans-serif'
      ctx.textBaseline = 'middle'
      ctx.setLineDash(this._punteada ? [4, 4] : dashDe(this._estilo.tipoLinea))
      for (const n of this._niveles) {
        ctx.beginPath()
        ctx.moveTo(izq, n.y)
        ctx.lineTo(der, n.y)
        ctx.stroke()
        ctx.fillText(n.etiqueta, der + 4, n.y)
      }
      ctx.setLineDash([])
    })
  }
}

class VistaFibonacci implements ISeriesPrimitivePaneView {
  private _renderer: RendererFibonacci
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
    estilo: EstiloDibujo,
  ) {
    this._chart = chart
    this._serie = serie
    this.p1 = p1
    this.p2 = p2
    this._renderer = new RendererFibonacci(estilo, punteada)
  }

  setEstilo(estilo: EstiloDibujo) {
    this._renderer.setEstilo(estilo)
  }

  update() {
    const ts = this._chart.timeScale()
    const x1 = ts.timeToCoordinate(this.p1.ts as unknown as Time)
    if (x1 == null) return

    let x2: number | null
    let precio2: number
    if (this.p2pixel) {
      x2 = this.p2pixel.x
      const pr = this._serie.coordinateToPrice(this.p2pixel.y)
      if (pr == null) return
      precio2 = pr
    } else {
      x2 = ts.timeToCoordinate(this.p2.ts as unknown as Time)
      precio2 = this.p2.precio
    }
    if (x2 == null) return

    const niveles: NivelDibujo[] = []
    for (const nivel of NIVELES_FIBONACCI) {
      const precio = this.p1.precio + (precio2 - this.p1.precio) * nivel
      const y = this._serie.priceToCoordinate(precio)
      if (y == null) continue
      niveles.push({ y, etiqueta: `${(nivel * 100).toFixed(1)}%  ${precio.toFixed(2)}` })
    }
    this._renderer.actualizar(x1, x2, niveles)
  }

  seleccionar(sel: boolean) {
    this._renderer.seleccionar(sel)
  }

  renderer() {
    return this._renderer
  }

  zOrder(): 'normal' {
    return 'normal'
  }
}

export class PrimitivaFibonacci implements ISeriesPrimitive {
  private _vista: VistaFibonacci
  private _requestUpdate?: () => void

  constructor(
    chart: IChartApi,
    serie: ISeriesApi<SeriesType>,
    p1: Punto,
    p2: Punto,
    punteada = false,
    estilo: EstiloDibujo = {},
  ) {
    this._vista = new VistaFibonacci(chart, serie, p1, p2, punteada, estilo)
  }

  actualizarEstilo(estilo: EstiloDibujo) {
    this._vista.setEstilo(estilo)
    this._requestUpdate?.()
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
