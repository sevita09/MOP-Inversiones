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
import type { LoteAbierto } from '../../api/tipos'

import type { Estilo } from '../../contextos/EstilosContext'
import { conOpacidad } from '../../contextos/EstilosContext'
import { dashDe } from './herramientas/estiloDibujo'
import { REC_PPC_COMPRA, REC_PPC_LINEA } from './config/estilosIndicadores'

const FONDO_ETIQUETA = '#0d1117'

export interface EstilosTenencia {
  compra: Estilo
  promedio: Estilo
}

function colorCon(estilo: Estilo, rec: Estilo): string {
  return conOpacidad(estilo.color ?? rec.color!, estilo.opacidad ?? rec.opacidad ?? 1)
}

const ESTILOS_DEFAULT: EstilosTenencia = { compra: REC_PPC_COMPRA, promedio: REC_PPC_LINEA }

interface LoteDibujable {
  x: number // dónde cae la compra en el eje de tiempo
  y: number // el precio al que se compró
  cantidad: number
}

/** Dibuja las compras abiertas de la cartera sobre el gráfico:
 *  - línea vertical punteada el día de la compra, con los papeles que quedan
 *  - línea horizontal punteada desde ese día hacia adelante, al precio pagado
 *  - línea llena con el PPC (precio promedio de compra) de toda la posición */
class RendererTenencia implements ISeriesPrimitivePaneRenderer {
  private _lotes: LoteDibujable[] = []
  private _yPpc: number | null = null
  private _estilos: EstilosTenencia = ESTILOS_DEFAULT

  setEstilos(estilos: EstilosTenencia) {
    this._estilos = estilos
  }

  actualizar(lotes: LoteDibujable[], yPpc: number | null) {
    this._lotes = lotes
    this._yPpc = yPpc
  }

  draw(target: CanvasRenderingTarget2D) {
    target.useBitmapCoordinateSpace((scope) => {
      const ctx = scope.context
      const ratio = scope.horizontalPixelRatio
      const ratioY = scope.verticalPixelRatio
      const ancho = scope.bitmapSize.width
      const alto = scope.bitmapSize.height

      ctx.save()
      const colorCompra = colorCon(this._estilos.compra, REC_PPC_COMPRA)
      const colorPpc = colorCon(this._estilos.promedio, REC_PPC_LINEA)
      const dashCompra = dashDe(this._estilos.compra.tipoLinea ?? 'dashed').map((n) => n * ratio)
      const dashPpc = dashDe(this._estilos.promedio.tipoLinea ?? 'solid').map((n) => n * ratio)

      for (const lote of this._lotes) {
        const x = Math.round(lote.x * ratio)
        const y = Math.round(lote.y * ratioY)

        // Vertical punteada en el día de la compra
        ctx.strokeStyle = colorCompra
        ctx.lineWidth = Math.max(1, Math.floor((this._estilos.compra.ancho ?? 1) * ratio))
        ctx.setLineDash(dashCompra)
        ctx.beginPath()
        ctx.moveTo(x, 0)
        ctx.lineTo(x, alto)
        ctx.stroke()

        // Horizontal punteada desde la compra hacia adelante, al precio pagado
        ctx.beginPath()
        ctx.moveTo(x, y)
        ctx.lineTo(ancho, y)
        ctx.stroke()

        this._etiqueta(
          ctx, x + 5 * ratio, y - 6 * ratioY,
          `${formatear(lote.cantidad)} papeles`, ratio, ratioY, colorCompra,
        )
      }

      // PPC: línea llena a lo ancho de todo el gráfico
      if (this._yPpc !== null) {
        const y = Math.round(this._yPpc * ratioY)
        ctx.setLineDash(dashPpc)
        ctx.strokeStyle = colorPpc
        ctx.lineWidth = Math.max(1, Math.floor((this._estilos.promedio.ancho ?? 2) * ratio))
        ctx.beginPath()
        ctx.moveTo(0, y)
        ctx.lineTo(ancho, y)
        ctx.stroke()
        this._etiqueta(ctx, 6 * ratio, y - 6 * ratioY, 'PPC', ratio, ratioY, colorPpc)
      }

      ctx.restore()
    })
  }

  private _etiqueta(
    ctx: CanvasRenderingContext2D,
    x: number,
    y: number,
    texto: string,
    ratio: number,
    ratioY: number,
    color: string,
  ) {
    ctx.setLineDash([])
    ctx.font = `${Math.round(11 * ratioY)}px system-ui, -apple-system, sans-serif`
    const ancho = ctx.measureText(texto).width + 8 * ratio
    const alto = 16 * ratioY

    ctx.fillStyle = FONDO_ETIQUETA
    ctx.fillRect(x, y - alto + 3 * ratioY, ancho, alto)
    ctx.strokeStyle = color
    ctx.lineWidth = Math.max(1, Math.floor(ratio))
    ctx.strokeRect(x, y - alto + 3 * ratioY, ancho, alto)

    ctx.fillStyle = color
    ctx.fillText(texto, x + 4 * ratio, y)
  }
}

function formatear(cantidad: number): string {
  return cantidad.toLocaleString('es-AR', { maximumFractionDigits: 2 })
}

class VistaTenencia implements ISeriesPrimitivePaneView {
  private _renderer = new RendererTenencia()
  private _chart: IChartApi
  private _serie: ISeriesApi<SeriesType>
  private _lotes: LoteAbierto[]
  private _ppc: number | null

  constructor(
    chart: IChartApi,
    serie: ISeriesApi<SeriesType>,
    lotes: LoteAbierto[],
    ppc: number | null,
  ) {
    this._chart = chart
    this._serie = serie
    this._lotes = lotes
    this._ppc = ppc
  }

  datos(lotes: LoteAbierto[], ppc: number | null) {
    this._lotes = lotes
    this._ppc = ppc
  }

  setEstilos(estilos: EstilosTenencia) {
    this._renderer.setEstilos(estilos)
  }

  update() {
    const escalaTiempo = this._chart.timeScale()
    const dibujables: LoteDibujable[] = []

    for (const lote of this._lotes) {
      if (lote.ts === null) continue
      const x = escalaTiempo.timeToCoordinate(lote.ts as Time)
      const y = this._serie.priceToCoordinate(lote.precio)
      if (x === null || y === null) continue
      dibujables.push({ x, y, cantidad: lote.cantidad })
    }

    const yPpc = this._ppc === null ? null : this._serie.priceToCoordinate(this._ppc)
    this._renderer.actualizar(dibujables, yPpc)
  }

  renderer() {
    return this._renderer
  }
}

export class PrimitivaTenencia implements ISeriesPrimitive<Time> {
  private _vista: VistaTenencia | null = null
  private _pedirActualizacion?: () => void
  private _chart: IChartApi
  private _serie: ISeriesApi<SeriesType>
  private _lotes: LoteAbierto[]
  private _ppc: number | null
  private _estilos: EstilosTenencia = ESTILOS_DEFAULT

  constructor(
    chart: IChartApi,
    serie: ISeriesApi<SeriesType>,
    lotes: LoteAbierto[] = [],
    ppc: number | null = null,
  ) {
    this._chart = chart
    this._serie = serie
    this._lotes = lotes
    this._ppc = ppc
  }

  attached(parametros: SeriesAttachedParameter<Time>) {
    this._pedirActualizacion = parametros.requestUpdate
    this._vista = new VistaTenencia(this._chart, this._serie, this._lotes, this._ppc)
    this._vista.setEstilos(this._estilos)
  }

  detached() {
    this._vista = null
    this._pedirActualizacion = undefined
  }

  actualizar(lotes: LoteAbierto[], ppc: number | null) {
    this._lotes = lotes
    this._ppc = ppc
    this._vista?.datos(lotes, ppc)
    this._pedirActualizacion?.()
  }

  setEstilos(estilos: EstilosTenencia) {
    this._estilos = estilos
    this._vista?.setEstilos(estilos)
    this._pedirActualizacion?.()
  }

  updateAllViews() {
    this._vista?.update()
  }

  paneViews() {
    return this._vista ? [this._vista] : []
  }
}
