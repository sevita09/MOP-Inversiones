import type { IChartApi, LogicalRange } from 'lightweight-charts'

export interface SincronizadorTiempo {
  registrar(chart: IChartApi): () => void
  volcarYSincronizar(chart: IChartApi, fn: () => void): void
}

export function crearSincronizadorTiempo(): SincronizadorTiempo {
  const charts = new Set<IChartApi>()
  let aplicando = false

  function registrar(chart: IChartApi): () => void {
    const alCambiar = (rango: LogicalRange | null) => {
      if (aplicando || rango == null) return
      aplicando = true
      for (const otro of charts) {
        if (otro !== chart) otro.timeScale().setVisibleLogicalRange(rango)
      }
      aplicando = false
    }
    chart.timeScale().subscribeVisibleLogicalRangeChange(alCambiar)
    charts.add(chart)

    return () => {
      chart.timeScale().unsubscribeVisibleLogicalRangeChange(alCambiar)
      charts.delete(chart)
    }
  }

  function volcarYSincronizar(chart: IChartApi, fn: () => void) {
    let rangoOrigen: LogicalRange | null = null
    for (const otro of charts) {
      if (otro === chart) continue
      rangoOrigen = otro.timeScale().getVisibleLogicalRange()
      if (rangoOrigen) break
    }

    aplicando = true
    fn()
    aplicando = false

    if (rangoOrigen) {
      requestAnimationFrame(() => {
        aplicando = true
        chart.timeScale().setVisibleLogicalRange(rangoOrigen)
        aplicando = false
      })
    }
  }

  return { registrar, volcarYSincronizar }
}
