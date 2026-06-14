import { useState } from 'react'
import InterruptorMoneda from '../componentes/InterruptorMoneda'
import LogoTicker from '../componentes/LogoTicker'
import PanelPrecio from '../componentes/grafico/PanelPrecio'
import SelectorTemporalidad from '../componentes/grafico/SelectorTemporalidad'
import SelectorTipoGrafico from '../componentes/grafico/SelectorTipoGrafico'
import { usarMoneda } from '../contextos/MonedaContext'
import { usarTicker } from '../contextos/TickerContext'
import type { Temporalidad, TipoGrafico } from '../api/tipos'
import './PaginaGrafico.css'

function PaginaGrafico() {
  const { moneda } = usarMoneda()
  const { ticker } = usarTicker()
  const [temporalidad, setTemporalidad] = useState<Temporalidad>('D')
  const [tipo, setTipo] = useState<TipoGrafico>('velas')

  return (
    <div className="pagina-grafico">
      <div className="barra-grafico">
        <span className="identidad-ticker">
          <LogoTicker ticker={ticker} tamano={24} />
          <span className="identidad-simbolo">{ticker}</span>
        </span>
        <SelectorTemporalidad temporalidad={temporalidad} alCambiar={setTemporalidad} />
        <span className="separador-barra" />
        <SelectorTipoGrafico tipo={tipo} alCambiar={setTipo} />
        <InterruptorMoneda />
      </div>
      <div className="pantalla-grafico">
        <PanelPrecio
          ticker={ticker}
          temporalidad={temporalidad}
          moneda={moneda}
          tipo={tipo}
        />
      </div>
    </div>
  )
}

export default PaginaGrafico
