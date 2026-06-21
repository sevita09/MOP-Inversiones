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

const COLOR = '#e3b341'
const COLOR_SELECCION = '#ffffff'

interface Punto {
  ts: number
  precio: number
}

interface Pixel {
  x: number
  y: number
}

class RendererTendencia implements ISeriesPrimitivePaneRenderer {
  private _p1x = 0
  private _p1y = 0
  private _p2x = 0
  private _p2y = 0
  private _punteada: boolean
  private _seleccionado = false

  constructor(punteada: boolean) {
    this._punteada = punteada
  }

  actualizar(p1x: number, p1y: number, p2x: number, p2y: number) {
    this._p1x = p1x
    this._p1y = p1y
    this._p2x = p2x
    this._p2y = p2y
  }

  seleccionar(sel: boolean) {
    this._seleccionado = sel
  }

  draw(target: CanvasRenderingTarget2D) {
    target.useMediaCoordinateSpace(({ context: ctx }) => {
      ctx.beginPath()
      ctx.strokeStyle = this._seleccionado ? COLOR_SELECCION : COLOR
      ctx.lineWidth = this._seleccionado ? 2 : 1
      ctx.setLineDash(this._punteada ? [4, 4] : [])
      ctx.moveTo(this._p1x, this._p1y)
      ctx.lineTo(this._p2x, this._p2y)
      ctx.stroke()
      ctx.setLineDash([])
    })
  }
}

class VistaTendencia implements ISeriesPrimitivePaneView {
  private _renderer: RendererTendencia
  private _serie: ISeriesApi<SeriesType>
  private _chart: IChartApi
  p1: Punto
  p2: Punto
  // Si está seteado, el segundo extremo se dibuja en píxeles (preview que sigue al mouse)
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
    this._renderer = new RendererTendencia(punteada)
  }

  update() {
    const ts = this._chart.timeScale()
    const x1 = ts.timeToCoordinate(this.p1.ts as unknown as Time)
    const y1 = this._serie.priceToCoordinate(this.p1.precio)
    if (x1 == null || y1 == null) return

    let x2: number | null
    let y2: number | null
    if (this.p2pixel) {
      x2 = this.p2pixel.x
      y2 = this.p2pixel.y
    } else {
      x2 = ts.timeToCoordinate(this.p2.ts as unknown as Time)
      y2 = this._serie.priceToCoordinate(this.p2.precio)
    }
    if (x2 == null || y2 == null) return
    this._renderer.actualizar(x1, y1, x2, y2)
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

export class PrimitivaTendencia implements ISeriesPrimitive {
  private _vista: VistaTendencia
  private _requestUpdate?: () => void

  constructor(
    chart: IChartApi,
    serie: ISeriesApi<SeriesType>,
    p1: Punto,
    p2: Punto,
    punteada = false,
  ) {
    this._vista = new VistaTendencia(chart, serie, p1, p2, punteada)
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

  // Mueve el segundo extremo en píxeles y repinta de inmediato (preview fluido)
  actualizarPixel(x: number, y: number) {
    this._vista.p2pixel = { x, y }
    this._requestUpdate?.()
  }

  seleccionar(sel: boolean) {
    this._vista.seleccionar(sel)
    this._requestUpdate?.()
  }
}
