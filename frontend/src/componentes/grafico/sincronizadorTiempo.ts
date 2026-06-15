import type { IChartApi, LogicalRange } from 'lightweight-charts'

// Mantiene varios charts (precio + osciladores) con el mismo rango temporal
// visible: cuando el usuario hace zoom o pan en uno, replica el rango en los
// demás. El flag `aplicando` corta el loop de reentrada entre suscripciones.
export interface SincronizadorTiempo {
  registrar(chart: IChartApi): () => void
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

    // Al entrar, alinearse con el rango de algún chart ya presente
    for (const otro of charts) {
      if (otro === chart) continue
      const rango = otro.timeScale().getVisibleLogicalRange()
      if (rango) chart.timeScale().setVisibleLogicalRange(rango)
      break
    }

    return () => {
      chart.timeScale().unsubscribeVisibleLogicalRangeChange(alCambiar)
      charts.delete(chart)
    }
  }

  return { registrar }
}
