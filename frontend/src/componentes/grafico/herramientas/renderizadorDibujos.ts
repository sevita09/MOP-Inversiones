import type {
  IChartApi,
  IPriceLine,
  ISeriesApi,
  SeriesType,
} from 'lightweight-charts'
import { LineStyle } from 'lightweight-charts'
import type { Dibujo } from '../../../api/cliente'

const COLOR_DIBUJO = '#e3b341'

interface LineaActiva {
  dibujoId: number
  priceLine: IPriceLine
}

export interface RenderizadorDibujos {
  sincronizar(dibujos: Dibujo[]): void
  destruir(): void
}

export function crearRenderizadorDibujos(
  _chart: IChartApi,
  serie: ISeriesApi<SeriesType>,
  alActualizar: (id: number, datos: Record<string, unknown>) => void,
  alEliminar: (id: number) => void,
): RenderizadorDibujos {
  const lineas = new Map<number, LineaActiva>()

  function sincronizar(dibujos: Dibujo[]) {
    const idsActuales = new Set(dibujos.map((d) => d.id))

    // Eliminar las que ya no existen
    for (const [id, linea] of lineas) {
      if (!idsActuales.has(id)) {
        try { serie.removePriceLine(linea.priceLine) } catch { /* serie disposed */ }
        lineas.delete(id)
      }
    }

    // Crear o actualizar
    for (const dibujo of dibujos) {
      if (dibujo.tipo === 'horizontal') {
        sincronizarHorizontal(dibujo)
      }
      // tendencia, fibonacci y medición se agregan en commits siguientes
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

  function destruir() {
    for (const linea of lineas.values()) {
      try { serie.removePriceLine(linea.priceLine) } catch { /* */ }
    }
    lineas.clear()
  }

  return { sincronizar, destruir }
}
