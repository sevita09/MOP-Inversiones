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
import type { OperacionGrafico } from '../../api/tipos'

const VERDE = '#3fb950'
const ROJO = '#f85149'
const FONDO = '#0d1117'

// La flecha se apoya a esta distancia del precio, del lado que no tapa la vela
const SEPARACION = 10
const ALTO_FLECHA = 9
const ANCHO_FLECHA = 12

interface FlechaDibujable {
  x: number
  y: number
  compra: boolean
  texto: string
}

/** Flechas de compra y venta sobre el precio al que se ejecutó cada orden.
 *
 *  A diferencia del PPC, que dibuja solo las compras que siguen abiertas, acá
 *  entran todas las operaciones —incluidas las de posiciones ya cerradas—
 *  porque la pregunta es cómo se operó, no qué se tiene. */
class RendererOperaciones implements ISeriesPrimitivePaneRenderer {
  private _flechas: FlechaDibujable[] = []

  actualizar(flechas: FlechaDibujable[]) {
    this._flechas = flechas
  }

  draw(target: CanvasRenderingTarget2D) {
    if (this._flechas.length === 0) return
    target.useBitmapCoordinateSpace((scope) => {
      const ctx = scope.context
      const ratio = scope.horizontalPixelRatio
      const ratioY = scope.verticalPixelRatio

      ctx.save()
      ctx.font = `${Math.round(10 * ratioY)}px system-ui, -apple-system, sans-serif`
      ctx.textAlign = 'center'

      for (const flecha of this._flechas) {
        const x = flecha.x * ratio
        const color = flecha.compra ? VERDE : ROJO
        // La compra apunta hacia arriba desde abajo del precio; la venta al revés
        const base = flecha.y * ratioY + (flecha.compra ? SEPARACION : -SEPARACION) * ratioY
        const punta = base + (flecha.compra ? -ALTO_FLECHA : ALTO_FLECHA) * ratioY

        ctx.fillStyle = color
        ctx.beginPath()
        ctx.moveTo(x, punta)
        ctx.lineTo(x - (ANCHO_FLECHA / 2) * ratio, base)
        ctx.lineTo(x + (ANCHO_FLECHA / 2) * ratio, base)
        ctx.closePath()
        ctx.fill()

        // La cantidad, del lado de afuera de la flecha
        const yTexto = base + (flecha.compra ? 13 : 3) * ratioY
        const ancho = ctx.measureText(flecha.texto).width + 6 * ratio
        ctx.fillStyle = FONDO
        ctx.fillRect(x - ancho / 2, yTexto - 9 * ratioY, ancho, 12 * ratioY)
        ctx.fillStyle = color
        ctx.fillText(flecha.texto, x, yTexto)
      }

      ctx.restore()
    })
  }
}

function cantidadCorta(cantidad: number): string {
  if (cantidad >= 1000) return `${Math.round(cantidad / 1000)}k`
  return `${Math.round(cantidad)}`
}

class VistaOperaciones implements ISeriesPrimitivePaneView {
  private _renderer = new RendererOperaciones()
  private _chart: IChartApi
  private _serie: ISeriesApi<SeriesType>
  private _operaciones: OperacionGrafico[]

  constructor(
    chart: IChartApi,
    serie: ISeriesApi<SeriesType>,
    operaciones: OperacionGrafico[],
  ) {
    this._chart = chart
    this._serie = serie
    this._operaciones = operaciones
  }

  datos(operaciones: OperacionGrafico[]) {
    this._operaciones = operaciones
  }

  update() {
    const escalaTiempo = this._chart.timeScale()
    const flechas: FlechaDibujable[] = []
    for (const operacion of this._operaciones) {
      if (operacion.ts === null) continue
      const x = escalaTiempo.timeToCoordinate(operacion.ts as Time)
      const y = this._serie.priceToCoordinate(operacion.precio)
      if (x === null || y === null) continue
      flechas.push({
        x,
        y,
        compra: operacion.tipo === 'compra',
        texto: cantidadCorta(operacion.cantidad),
      })
    }
    this._renderer.actualizar(flechas)
  }

  renderer() {
    return this._renderer
  }
}

export class PrimitivaOperaciones implements ISeriesPrimitive<Time> {
  private _vista: VistaOperaciones | null = null
  private _pedirActualizacion?: () => void
  private _chart: IChartApi
  private _serie: ISeriesApi<SeriesType>
  private _operaciones: OperacionGrafico[]

  constructor(
    chart: IChartApi,
    serie: ISeriesApi<SeriesType>,
    operaciones: OperacionGrafico[] = [],
  ) {
    this._chart = chart
    this._serie = serie
    this._operaciones = operaciones
  }

  attached(parametros: SeriesAttachedParameter<Time>) {
    this._pedirActualizacion = parametros.requestUpdate
    this._vista = new VistaOperaciones(this._chart, this._serie, this._operaciones)
  }

  detached() {
    this._vista = null
    this._pedirActualizacion = undefined
  }

  actualizar(operaciones: OperacionGrafico[]) {
    this._operaciones = operaciones
    this._vista?.datos(operaciones)
    this._pedirActualizacion?.()
  }

  updateAllViews() {
    this._vista?.update()
  }

  paneViews() {
    return this._vista ? [this._vista] : []
  }
}
