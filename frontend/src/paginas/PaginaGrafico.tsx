import { useRef, useState } from 'react'
import InterruptorMoneda from '../componentes/InterruptorMoneda'
import LogoTicker from '../componentes/LogoTicker'
import PanelPrecio, { type PanelPrecioHandle } from '../componentes/grafico/PanelPrecio'
import SelectorTemporalidad from '../componentes/grafico/SelectorTemporalidad'
import SelectorTipoGrafico from '../componentes/grafico/SelectorTipoGrafico'
import SelectorEscala from '../componentes/grafico/SelectorEscala'
import SelectorVolumen from '../componentes/grafico/SelectorVolumen'
import SelectorPeriodo from '../componentes/grafico/SelectorPeriodo'
import { usarMoneda } from '../contextos/MonedaContext'
import { usarTicker } from '../contextos/TickerContext'
import { usarAtajosTeclado } from '../hooks/usarAtajosTeclado'
import type { EscalaPrecio, Temporalidad, TipoGrafico } from '../api/tipos'
import './PaginaGrafico.css'

function PaginaGrafico() {
  const { moneda } = usarMoneda()
  const { ticker } = usarTicker()
  const [temporalidad, setTemporalidad] = useState<Temporalidad>('D')
  usarAtajosTeclado(setTemporalidad)
  const [tipo, setTipo] = useState<TipoGrafico>('velas')
  const [escala, setEscala] = useState<EscalaPrecio>('lineal')
  const [mostrarVolumen, setMostrarVolumen] = useState(true)
  const panelRef = useRef<PanelPrecioHandle>(null)

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
        <span className="separador-barra" />
        <SelectorVolumen mostrar={mostrarVolumen} alCambiar={setMostrarVolumen} />
        <span className="separador-barra" />
        <SelectorPeriodo alElegir={(meses) => panelRef.current?.verRango(meses)} />
        <InterruptorMoneda />
      </div>
      <div className="pantalla-grafico">
        <PanelPrecio
          ref={panelRef}
          ticker={ticker}
          temporalidad={temporalidad}
          moneda={moneda}
          tipo={tipo}
          escala={escala}
          mostrarVolumen={mostrarVolumen}
        />
        <div className="escala-overlay">
          <SelectorEscala escala={escala} alCambiar={setEscala} />
        </div>
      </div>
    </div>
  )
}

export default PaginaGrafico
