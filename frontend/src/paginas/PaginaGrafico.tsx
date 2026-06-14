import { useState } from 'react'
import InterruptorMoneda from '../componentes/InterruptorMoneda'
import LogoTicker from '../componentes/LogoTicker'
import PanelPrecio from '../componentes/grafico/PanelPrecio'
import SelectorTemporalidad from '../componentes/grafico/SelectorTemporalidad'
import { usarMoneda } from '../contextos/MonedaContext'
import { usarTicker } from '../contextos/TickerContext'
import type { Temporalidad } from '../api/tipos'
import './PaginaGrafico.css'

function PaginaGrafico() {
  const { moneda } = usarMoneda()
  const { ticker } = usarTicker()
  const [temporalidad, setTemporalidad] = useState<Temporalidad>('D')

  return (
    <div className="pagina-grafico">
      <div className="barra-grafico">
        <span className="identidad-ticker">
          <LogoTicker ticker={ticker} tamano={24} />
          <span className="identidad-simbolo">{ticker}</span>
        </span>
        <SelectorTemporalidad temporalidad={temporalidad} alCambiar={setTemporalidad} />
        <InterruptorMoneda />
      </div>
      <div className="pantalla-grafico">
        <PanelPrecio ticker={ticker} temporalidad={temporalidad} moneda={moneda} />
      </div>
    </div>
  )
}

export default PaginaGrafico
