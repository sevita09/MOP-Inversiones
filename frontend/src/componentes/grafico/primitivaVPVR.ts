import type {
  ISeriesApi,
  ISeriesPrimitive,
  ISeriesPrimitivePaneRenderer,
  ISeriesPrimitivePaneView,
  SeriesAttachedParameter,
  SeriesType,
  Time,
} from 'lightweight-charts'
import type { CanvasRenderingTarget2D } from 'fancy-canvas'
import type { PerfilVPVR } from './vpvr'
import { conOpacidad, type Estilo } from '../../contextos/EstilosContext'
import { dashDe } from './herramientas/estiloDibujo'
import {
  REC_VPVR_BAJA,
  REC_VPVR_POC,
  REC_VPVR_SUBE,
} from './config/estilosIndicadores'

const ANCHO_MAX_FRAC = 0.15 // ancho de la barra más larga = 15% del panel

// Estilo efectivo de cada pieza del VPVR (histogramas + línea del POC)
export interface EstilosVPVR {
  sube: Estilo
  baja: Estilo
  poc: Estilo
}

function colorCon(estilo: Estilo, rec: Estilo): string {
  return conOpacidad(estilo.color ?? rec.color!, estilo.opacidad ?? rec.opacidad ?? 1)
}

interface BarraPixel {
  yTop: number
  yBot: number
  subeFrac: number // 0..1 respecto del volumen máximo
  bajaFrac: number
}

// --- Barras del histograma (detrás de las velas) ---

class RendererBarras implements ISeriesPrimitivePaneRenderer {
  private _barras: BarraPixel[] = []
  private _colorSube = colorCon(REC_VPVR_SUBE, REC_VPVR_SUBE)
  private _colorBaja = colorCon(REC_VPVR_BAJA, REC_VPVR_BAJA)

  setBarras(barras: BarraPixel[]) {
    this._barras = barras
  }

  setColores(sube: string, baja: string) {
    this._colorSube = sube
    this._colorBaja = baja
  }

  draw(target: CanvasRenderingTarget2D) {
    target.useMediaCoordinateSpace(({ context: ctx, mediaSize }) => {
      const anchoMax = mediaSize.width * ANCHO_MAX_FRAC
      const der = mediaSize.width // pegado al borde derecho (junto al eje de precios)
      for (const b of this._barras) {
        const alto = Math.max(1, b.yBot - b.yTop - 1) // -1px de separación entre barras
        const subeW = b.subeFrac * anchoMax
        const bajaW = b.bajaFrac * anchoMax
        // Alcista pegado a la derecha; bajista a su izquierda
        ctx.fillStyle = this._colorSube
        ctx.fillRect(der - subeW, b.yTop, subeW, alto)
        ctx.fillStyle = this._colorBaja
        ctx.fillRect(der - subeW - bajaW, b.yTop, bajaW, alto)
      }
    })
  }
}

// --- Línea del POC (sobre las velas) ---

class RendererPoc implements ISeriesPrimitivePaneRenderer {
  private _y: number | null = null
  private _color = colorCon(REC_VPVR_POC, REC_VPVR_POC)
  private _ancho = REC_VPVR_POC.ancho ?? 2
  private _dash: number[] = []

  setY(y: number | null) {
    this._y = y
  }

  setEstilo(color: string, ancho: number, dash: number[]) {
    this._color = color
    this._ancho = ancho
    this._dash = dash
  }

  draw(target: CanvasRenderingTarget2D) {
    if (this._y == null) return
    const y = this._y
    target.useMediaCoordinateSpace(({ context: ctx, mediaSize }) => {
      ctx.strokeStyle = this._color
      ctx.lineWidth = this._ancho
      ctx.setLineDash(this._dash)
      ctx.beginPath()
      ctx.moveTo(0, y)
      ctx.lineTo(mediaSize.width, y)
      ctx.stroke()
      ctx.setLineDash([])
    })
  }
}

class VistaBarras implements ISeriesPrimitivePaneView {
  private _r = new RendererBarras()
  setBarras(barras: BarraPixel[]) {
    this._r.setBarras(barras)
  }
  setColores(sube: string, baja: string) {
    this._r.setColores(sube, baja)
  }
  renderer() {
    return this._r
  }
  zOrder(): 'bottom' {
    return 'bottom'
  }
}

class VistaPoc implements ISeriesPrimitivePaneView {
  private _r = new RendererPoc()
  setY(y: number | null) {
    this._r.setY(y)
  }
  setEstilo(color: string, ancho: number, dash: number[]) {
    this._r.setEstilo(color, ancho, dash)
  }
  renderer() {
    return this._r
  }
  zOrder(): 'top' {
    return 'top'
  }
}

export class PrimitivaVPVR implements ISeriesPrimitive {
  private _serie: ISeriesApi<SeriesType>
  private _perfil: PerfilVPVR | null = null
  private _barras = new VistaBarras()
  private _poc = new VistaPoc()
  private _requestUpdate?: () => void

  constructor(serie: ISeriesApi<SeriesType>) {
    this._serie = serie
  }

  attached(param: SeriesAttachedParameter<Time>) {
    this._requestUpdate = param.requestUpdate
  }

  detached() {
    this._requestUpdate = undefined
  }

  paneViews() {
    return [this._barras, this._poc]
  }

  updateAllViews() {
    const p = this._perfil
    if (!p || p.paso <= 0 || p.maxVolumen <= 0) {
      this._barras.setBarras([])
      this._poc.setY(null)
      return
    }
    const barras: BarraPixel[] = []
    for (let b = 0; b < p.bins.length; b++) {
      // Bordes del bin en coordenadas de precio → píxeles (respeta escala log)
      const yTop = this._serie.priceToCoordinate(p.min + p.paso * (b + 1))
      const yBot = this._serie.priceToCoordinate(p.min + p.paso * b)
      if (yTop == null || yBot == null) continue
      barras.push({
        yTop,
        yBot,
        subeFrac: p.bins[b].volumenSube / p.maxVolumen,
        bajaFrac: p.bins[b].volumenBaja / p.maxVolumen,
      })
    }
    this._barras.setBarras(barras)
    const pocY = this._serie.priceToCoordinate(p.bins[p.pocIndice].precio)
    this._poc.setY(pocY ?? null)
  }

  setPerfil(perfil: PerfilVPVR | null) {
    this._perfil = perfil
    this._requestUpdate?.()
  }

  // Aplica el estilo del usuario (colores/opacidad de los histogramas, línea del POC)
  setEstilos(estilos: EstilosVPVR) {
    this._barras.setColores(
      colorCon(estilos.sube, REC_VPVR_SUBE),
      colorCon(estilos.baja, REC_VPVR_BAJA),
    )
    this._poc.setEstilo(
      colorCon(estilos.poc, REC_VPVR_POC),
      estilos.poc.ancho ?? REC_VPVR_POC.ancho ?? 2,
      dashDe(estilos.poc.tipoLinea),
    )
    this._requestUpdate?.()
  }
}
