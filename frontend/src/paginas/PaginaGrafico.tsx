import { useEffect, useRef } from 'react'
import InterruptorMoneda from '../componentes/InterruptorMoneda'
import LogoTicker from '../componentes/LogoTicker'
import PanelPrecio, { type PanelPrecioHandle } from '../componentes/grafico/PanelPrecio'
import SelectorTemporalidad from '../componentes/grafico/SelectorTemporalidad'
import SelectorTipoGrafico from '../componentes/grafico/SelectorTipoGrafico'
import SelectorEscala from '../componentes/grafico/SelectorEscala'
import SelectorVolumen from '../componentes/grafico/SelectorVolumen'
import SelectorEma from '../componentes/grafico/SelectorEma'
import SelectorBandas from '../componentes/grafico/SelectorBandas'
import SelectorPeriodo from '../componentes/grafico/SelectorPeriodo'
import BotonPantallaCompleta from '../componentes/grafico/BotonPantallaCompleta'
import { usarMoneda } from '../contextos/MonedaContext'
import { usarTicker } from '../contextos/TickerContext'
import { usarAtajosTeclado } from '../hooks/usarAtajosTeclado'
import { usarEstadoPersistente } from '../hooks/usarEstadoPersistente'
import { usarPantallaCompleta } from '../hooks/usarPantallaCompleta'
import type { EscalaPrecio, Temporalidad, TipoGrafico } from '../api/tipos'
import './PaginaGrafico.css'

// Los tickers de dólar (CCL/oficial) no tienen intradía: solo D, S y M
const TEMPORALIDADES_DOLAR: Temporalidad[] = ['D', 'S', 'M']

function esTickerDolar(ticker: string): boolean {
  return ticker.startsWith('DOLAR')
}

function PaginaGrafico() {
  const { moneda } = usarMoneda()
  const { ticker } = usarTicker()
  const [temporalidad, setTemporalidad] = usarEstadoPersistente<Temporalidad>('mop.temporalidad', 'D')
  usarAtajosTeclado(setTemporalidad)
  const [tipo, setTipo] = usarEstadoPersistente<TipoGrafico>('mop.tipo', 'velas')
  const [escala, setEscala] = usarEstadoPersistente<EscalaPrecio>('mop.escala', 'lineal')
  const [mostrarVolumen, setMostrarVolumen] = usarEstadoPersistente('mop.volumen', true)
  const [mostrarEma, setMostrarEma] = usarEstadoPersistente('mop.ema', false)
  const [mostrarBandas, setMostrarBandas] = usarEstadoPersistente('mop.bandas', false)
  const panelRef = useRef<PanelPrecioHandle>(null)
  const paginaRef = useRef<HTMLDivElement>(null)
  const pantalla = usarPantallaCompleta(paginaRef)

  const disponibles = esTickerDolar(ticker) ? TEMPORALIDADES_DOLAR : undefined

  // Si la temporalidad activa no aplica al ticker (p.ej. 1H en un dólar), pasar a D
  useEffect(() => {
    if (disponibles && !disponibles.includes(temporalidad)) {
      setTemporalidad('D')
    }
  }, [disponibles, temporalidad, setTemporalidad])

  return (
    <div className="pagina-grafico" ref={paginaRef}>
      <div className="barra-grafico">
        <span className="identidad-ticker">
          <LogoTicker ticker={ticker} tamano={24} />
          <span className="identidad-simbolo">{ticker}</span>
        </span>
        <SelectorTemporalidad
          temporalidad={temporalidad}
          alCambiar={setTemporalidad}
          disponibles={disponibles}
        />
        <span className="separador-barra" />
        <SelectorTipoGrafico tipo={tipo} alCambiar={setTipo} />
        <span className="separador-barra" />
        <SelectorVolumen mostrar={mostrarVolumen} alCambiar={setMostrarVolumen} />
        <SelectorEma mostrar={mostrarEma} alCambiar={setMostrarEma} />
        <SelectorBandas mostrar={mostrarBandas} alCambiar={setMostrarBandas} />
        <span className="separador-barra" />
        <SelectorPeriodo alElegir={(meses) => panelRef.current?.verRango(meses)} />
        <InterruptorMoneda />
        <BotonPantallaCompleta activa={pantalla.activa} alAlternar={pantalla.alternar} />
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
          mostrarEma={mostrarEma}
          mostrarBandas={mostrarBandas}
        />
        <div className="escala-overlay">
          <SelectorEscala escala={escala} alCambiar={setEscala} />
        </div>
      </div>
    </div>
  )
}

export default PaginaGrafico
