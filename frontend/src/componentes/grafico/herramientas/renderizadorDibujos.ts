import type {
  IChartApi,
  IPriceLine,
  ISeriesApi,
  SeriesType,
} from 'lightweight-charts'
import { LineStyle } from 'lightweight-charts'
import type { Dibujo } from '../../../api/cliente'
import { PrimitivaTendencia } from './primitivaTendencia'

const COLOR_DIBUJO = '#e3b341'

interface LineaActiva {
  dibujoId: number
  priceLine: IPriceLine
}

interface PrimitivaActiva {
  dibujoId: number
  primitiva: PrimitivaTendencia
}

interface Punto {
  ts: number
  precio: number
}

export interface RenderizadorDibujos {
  sincronizar(dibujos: Dibujo[]): void
  previsualizarTendencia(p1: Punto, x: number, y: number): void
  limpiarPrevisualizacion(): void
  destruir(): void
}

export function crearRenderizadorDibujos(
  chart: IChartApi,
  serie: ISeriesApi<SeriesType>,
  _alActualizar: (id: number, datos: Record<string, unknown>) => void,
  _alEliminar: (id: number) => void,
): RenderizadorDibujos {
  const lineas = new Map<number, LineaActiva>()
  const primitivas = new Map<number, PrimitivaActiva>()
  let previa: PrimitivaTendencia | null = null

  function sincronizar(dibujos: Dibujo[]) {
    const idsActuales = new Set(dibujos.map((d) => d.id))

    for (const [id, linea] of lineas) {
      if (!idsActuales.has(id)) {
        try { serie.removePriceLine(linea.priceLine) } catch { /* */ }
        lineas.delete(id)
      }
    }
    for (const [id, p] of primitivas) {
      if (!idsActuales.has(id)) {
        try { serie.detachPrimitive(p.primitiva) } catch { /* */ }
        primitivas.delete(id)
      }
    }

    for (const dibujo of dibujos) {
      if (dibujo.tipo === 'horizontal') sincronizarHorizontal(dibujo)
      else if (dibujo.tipo === 'tendencia') sincronizarTendencia(dibujo)
    }
  }

  function sincronizarHorizontal(dibujo: Dibujo) {
    const precio = dibujo.datos.precio as number
    const color = (dibujo.datos.color as string) ?? COLOR_DIBUJO
    const existente = lineas.get(dibujo.id)
    if (existente) {
      existente.priceLine.applyOptions({ price: precio, color })
      return
    }
    const priceLine = serie.createPriceLine({
      price: precio,
      color,
      lineWidth: 1,
      lineStyle: LineStyle.Solid,
      axisLabelVisible: true,
      title: '',
    })
    lineas.set(dibujo.id, { dibujoId: dibujo.id, priceLine })
  }

  function sincronizarTendencia(dibujo: Dibujo) {
    const p1 = dibujo.datos.p1 as { ts: number; precio: number }
    const p2 = dibujo.datos.p2 as { ts: number; precio: number }
    const existente = primitivas.get(dibujo.id)
    if (existente) {
      existente.primitiva.actualizar(p1, p2)
      return
    }
    const primitiva = new PrimitivaTendencia(chart, serie, p1, p2)
    serie.attachPrimitive(primitiva)
    primitivas.set(dibujo.id, { dibujoId: dibujo.id, primitiva })
  }

  function previsualizarTendencia(p1: Punto, x: number, y: number) {
    if (!previa) {
      previa = new PrimitivaTendencia(chart, serie, p1, p1, true)
      serie.attachPrimitive(previa)
    }
    previa.actualizarPixel(x, y)
  }

  function limpiarPrevisualizacion() {
    if (previa) {
      try { serie.detachPrimitive(previa) } catch { /* */ }
      previa = null
    }
  }

  function destruir() {
    limpiarPrevisualizacion()
    for (const linea of lineas.values()) {
      try { serie.removePriceLine(linea.priceLine) } catch { /* */ }
    }
    for (const p of primitivas.values()) {
      try { serie.detachPrimitive(p.primitiva) } catch { /* */ }
    }
    lineas.clear()
    primitivas.clear()
  }

  return { sincronizar, previsualizarTendencia, limpiarPrevisualizacion, destruir }
}
