import type { ISeriesApi, IPriceLine, LineWidth, SeriesType } from 'lightweight-charts'
import { LineStyle } from 'lightweight-charts'
import type { NivelSwing } from '../../api/cliente'

const COLOR_SOPORTE = '#3fb950'
const COLOR_RESISTENCIA = '#f85149'
const COLOR_MIXTO = '#8b949e'

function color(tipo: NivelSwing['tipo']): string {
  if (tipo === 'soporte') return COLOR_SOPORTE
  if (tipo === 'resistencia') return COLOR_RESISTENCIA
  return COLOR_MIXTO
}

// Los niveles de temporalidad superior (semanal/mensual) van más marcados:
// línea sólida y más gruesa; los del propio timeframe, finos y punteados.
export function dibujarNiveles(
  serie: ISeriesApi<SeriesType>,
  niveles: NivelSwing[],
): IPriceLine[] {
  return niveles.map((nivel) => {
    const macro = nivel.origen === 'S' || nivel.origen === 'M'
    const ancho: LineWidth = macro ? 2 : 1
    return serie.createPriceLine({
      price: nivel.precio,
      color: color(nivel.tipo),
      lineWidth: ancho,
      lineStyle: macro ? LineStyle.Solid : LineStyle.Dashed,
      axisLabelVisible: true,
      title: `${nivel.origen}·${nivel.contactos}`,
    })
  })
}

export function quitarNiveles(serie: ISeriesApi<SeriesType>, lineas: IPriceLine[]): void {
  for (const linea of lineas) {
    try {
      serie.removePriceLine(linea)
    } catch {
      /* serie liberada */
    }
  }
}
