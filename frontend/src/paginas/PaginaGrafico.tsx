import { useCallback, useEffect, useRef, useState } from 'react'
import InterruptorMoneda from '../componentes/InterruptorMoneda'
import LogoTicker from '../componentes/LogoTicker'
import PanelPrecio, { type PanelPrecioHandle } from '../componentes/grafico/PanelPrecio'
import PanelOscilador from '../componentes/grafico/PanelOscilador'
import CapaDibujos from '../componentes/grafico/herramientas/CapaDibujos'
import MenuIndicadores from '../componentes/grafico/MenuIndicadores'
import { OSCILADORES, ORDEN_OSCILADORES } from '../componentes/grafico/configOsciladores'
import type { NombreOscilador } from '../componentes/grafico/configOsciladores'
import { crearSincronizadorTiempo } from '../componentes/grafico/sincronizadorTiempo'
import SelectorTemporalidad from '../componentes/grafico/SelectorTemporalidad'
import SelectorTipoGrafico from '../componentes/grafico/SelectorTipoGrafico'
import SelectorEscala from '../componentes/grafico/SelectorEscala'
import SelectorVolumen from '../componentes/grafico/SelectorVolumen'
import SelectorEma from '../componentes/grafico/SelectorEma'
import SelectorBandas from '../componentes/grafico/SelectorBandas'
import SelectorBollinger from '../componentes/grafico/SelectorBollinger'
import SelectorNiveles from '../componentes/grafico/SelectorNiveles'
import SelectorPeriodo from '../componentes/grafico/SelectorPeriodo'
import BotonPantallaCompleta from '../componentes/grafico/BotonPantallaCompleta'
import DialogoConfig from '../componentes/grafico/config/DialogoConfig'
import BotonTuerca from '../componentes/grafico/config/BotonTuerca'
import {
  APERTURA_PRECIO,
  type AperturaConfig,
} from '../componentes/grafico/config/estilosIndicadores'
import { usarMonedaEfectiva } from '../hooks/usarMonedaEfectiva'
import { usarAdr } from '../hooks/usarAdr'
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
  const { moneda } = usarMonedaEfectiva()
  const { ticker } = usarTicker()
  const adr = usarAdr(ticker)
  const [temporalidad, setTemporalidad] = usarEstadoPersistente<Temporalidad>('mop.temporalidad', 'D')
  usarAtajosTeclado(setTemporalidad)
  const [tipo, setTipo] = usarEstadoPersistente<TipoGrafico>('mop.tipo', 'velas')
  const [escala, setEscala] = usarEstadoPersistente<EscalaPrecio>('mop.escala', 'lineal')
  const [mostrarVolumen, setMostrarVolumen] = usarEstadoPersistente('mop.volumen', true)
  const [mostrarEma, setMostrarEma] = usarEstadoPersistente('mop.ema', false)
  const [mostrarBandas, setMostrarBandas] = usarEstadoPersistente('mop.bandas', false)
  const [mostrarBollinger, setMostrarBollinger] = usarEstadoPersistente('mop.bollinger', false)
  const [mostrarNiveles, setMostrarNiveles] = usarEstadoPersistente('mop.niveles', false)
  const [oscActivos, setOscActivos] = usarEstadoPersistente<NombreOscilador[]>('mop.osciladores', [])
  const osciladores = new Set(oscActivos)
  const alternarOscilador = (nombre: NombreOscilador, activo: boolean) => {
    const siguiente = new Set(oscActivos)
    activo ? siguiente.add(nombre) : siguiente.delete(nombre)
    setOscActivos([...siguiente])
  }
  const panelRef = useRef<PanelPrecioHandle>(null)
  const paginaRef = useRef<HTMLDivElement>(null)
  const pantalla = usarPantallaCompleta(paginaRef)
  // Un único sincronizador mantiene el precio y los osciladores con el mismo zoom
  const [sincronizador] = useState(crearSincronizadorTiempo)
  // ts bajo el crosshair, compartido: cada panel muestra su valor en ese punto
  const [tsActivo, setTsActivo] = useState<number | null>(null)
  // Config de estilo abierta (tuerca de la barra o de un oscilador); null = cerrada
  const [configEstilo, setConfigEstilo] = useState<AperturaConfig | null>(null)
  const obtenerChart = useCallback(() => panelRef.current?.obtenerChart() ?? null, [])
  const obtenerSerie = useCallback(() => panelRef.current?.obtenerSerie() ?? null, [])

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
        <SelectorNiveles mostrar={mostrarNiveles} alCambiar={setMostrarNiveles} />
        <SelectorEma mostrar={mostrarEma} temporalidad={temporalidad} alCambiar={setMostrarEma} />
        <SelectorBandas mostrar={mostrarBandas} alCambiar={setMostrarBandas} />
        <SelectorBollinger mostrar={mostrarBollinger} alCambiar={setMostrarBollinger} />
        <BotonTuerca
          titulo="Configurar EMA, σ y Bollinger"
          alTocar={() => setConfigEstilo(APERTURA_PRECIO)}
        />
        <span className="separador-barra" />
        <MenuIndicadores
          activos={osciladores}
          alAlternar={alternarOscilador}
          alConfigurar={setConfigEstilo}
        />
        <span className="separador-barra" />
        <SelectorPeriodo alElegir={(meses) => panelRef.current?.verRango(meses)} />
        <InterruptorMoneda />
        <BotonPantallaCompleta activa={pantalla.activa} alAlternar={pantalla.alternar} />
      </div>
      <div className="pantalla-grafico">
        <div className="area-precio">
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
            mostrarBollinger={mostrarBollinger}
            mostrarNiveles={mostrarNiveles}
            sincronizador={sincronizador}
            tsActivo={tsActivo}
            alMoverCrosshair={setTsActivo}
          />
          <CapaDibujos
            ticker={ticker}
            obtenerChart={obtenerChart}
            obtenerSerie={obtenerSerie}
          />
          <div className="escala-overlay">
            <SelectorEscala escala={escala} alCambiar={setEscala} />
          </div>
          {moneda === 'USD' && adr && (
            <span className="adr-overlay">
              ADR {adr.simbolo} · {adr.ratio}:1
            </span>
          )}
        </div>
        {ORDEN_OSCILADORES.filter((n) => osciladores.has(n)).map((nombre) => (
          <PanelOscilador
            key={nombre}
            config={OSCILADORES[nombre]}
            ticker={ticker}
            temporalidad={temporalidad}
            moneda={moneda}
            sincronizador={sincronizador}
            tsActivo={tsActivo}
            alMoverCrosshair={setTsActivo}
          />
        ))}
      </div>
      {configEstilo && (
        <DialogoConfig
          apertura={configEstilo}
          temporalidad={temporalidad}
          alCerrar={() => setConfigEstilo(null)}
        />
      )}
    </div>
  )
}

export default PaginaGrafico
