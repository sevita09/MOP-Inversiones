import { useState } from 'react'
import InterruptorMoneda from '../componentes/InterruptorMoneda'
import PanelPrecio from '../componentes/grafico/PanelPrecio'
import SelectorTemporalidad from '../componentes/grafico/SelectorTemporalidad'
import { usarMoneda } from '../contextos/MonedaContext'
import type { Temporalidad } from '../api/tipos'

function PaginaGrafico() {
  const { moneda } = usarMoneda()
  const [temporalidad, setTemporalidad] = useState<Temporalidad>('D')

  return (
    <div className="pagina-grafico">
      <div className="barra-grafico">
        <SelectorTemporalidad temporalidad={temporalidad} alCambiar={setTemporalidad} />
        <InterruptorMoneda />
      </div>
      <div className="pantalla-grafico">
        <PanelPrecio ticker="GGAL" temporalidad={temporalidad} moneda={moneda} />
      </div>
    </div>
  )
}

export default PaginaGrafico
