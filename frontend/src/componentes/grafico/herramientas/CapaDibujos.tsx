import { useCallback, useEffect, useRef, useState } from 'react'
import type { IChartApi, ISeriesApi, MouseEventParams, SeriesType } from 'lightweight-charts'
import type { Dibujo } from '../../../api/cliente'
import { usarDibujos } from '../../../hooks/usarDibujos'
import { crearRenderizadorDibujos, type RenderizadorDibujos } from './renderizadorDibujos'
import BarraHerramientas from './BarraHerramientas'
import type { TipoHerramienta } from './tipos'

interface Props {
  ticker: string
  obtenerChart: () => IChartApi | null
  obtenerSerie: () => ISeriesApi<SeriesType> | null
}

function CapaDibujos({ ticker, obtenerChart, obtenerSerie }: Props) {
  const { dibujos, agregar, actualizar, eliminar } = usarDibujos(ticker)
  const [herramienta, setHerramienta] = useState<TipoHerramienta>(null)
  const renderizador = useRef<RenderizadorDibujos | null>(null)
  const herramientaRef = useRef(herramienta)
  herramientaRef.current = herramienta
  const agregarRef = useRef(agregar)
  agregarRef.current = agregar

  // Crear/destruir renderizador cuando el chart está listo
  useEffect(() => {
    const chart = obtenerChart()
    const serie = obtenerSerie()
    if (!chart || !serie) return
    const r = crearRenderizadorDibujos(chart, serie, actualizar, eliminar)
    renderizador.current = r
    return () => {
      r.destruir()
      renderizador.current = null
    }
  }, [obtenerChart, obtenerSerie, actualizar, eliminar])

  // Sincronizar dibujos con el renderizador
  useEffect(() => {
    renderizador.current?.sincronizar(dibujos)
  }, [dibujos])

  // Click en el chart para agregar dibujos
  useEffect(() => {
    const chart = obtenerChart()
    if (!chart) return

    const alClick = (params: MouseEventParams) => {
      const tipo = herramientaRef.current
      if (!tipo) return
      const serie = obtenerSerie()
      if (!serie || !params.point) return

      if (tipo === 'horizontal') {
        const coord = serie.coordinateToPrice(params.point.y)
        if (coord == null || !isFinite(coord)) return
        agregarRef.current('horizontal', { precio: Math.round(coord * 100) / 100 })
        setHerramienta(null)
      }
    }

    chart.subscribeClick(alClick)
    return () => chart.unsubscribeClick(alClick)
  }, [obtenerChart, obtenerSerie])

  const borrarTodo = useCallback(async () => {
    for (const d of dibujos) {
      await eliminar(d.id)
    }
  }, [dibujos, eliminar])

  return (
    <BarraHerramientas
      activa={herramienta}
      alSeleccionar={setHerramienta}
      alBorrarTodo={borrarTodo}
    />
  )
}

export default CapaDibujos
