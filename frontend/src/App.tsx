import { useState } from 'react'
import EstadoBackend from './componentes/EstadoBackend'
import InterruptorMoneda from './componentes/InterruptorMoneda'
import PanelPrecio from './componentes/grafico/PanelPrecio'
import SelectorTemporalidad from './componentes/grafico/SelectorTemporalidad'
import { usarMoneda } from './contextos/MonedaContext'
import type { Temporalidad } from './api/tipos'

function App() {
  const { moneda } = usarMoneda()
  const [temporalidad, setTemporalidad] = useState<Temporalidad>('D')

  return (
    <div className="app">
      <header className="encabezado">
        <img src="/logo.png" alt="MOP Inversiones" className="logo-encabezado" />
        <span className="titulo-encabezado">MOP - Inversiones</span>
        <SelectorTemporalidad temporalidad={temporalidad} alCambiar={setTemporalidad} />
        <EstadoBackend />
        <InterruptorMoneda />
      </header>
      <main className="pantalla-grafico">
        <PanelPrecio ticker="GGAL" temporalidad={temporalidad} moneda={moneda} />
      </main>
    </div>
  )
}

export default App
