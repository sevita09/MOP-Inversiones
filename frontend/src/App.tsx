import EstadoBackend from './componentes/EstadoBackend'
import InterruptorMoneda from './componentes/InterruptorMoneda'
import PanelPrecio from './componentes/grafico/PanelPrecio'
import { usarMoneda } from './contextos/MonedaContext'

function App() {
  const { moneda } = usarMoneda()

  return (
    <div className="app">
      <header className="encabezado">
        <img src="/logo.png" alt="MOP Inversiones" className="logo-encabezado" />
        <span className="titulo-encabezado">MOP - Inversiones</span>
        <EstadoBackend />
        <InterruptorMoneda />
      </header>
      <main className="pantalla-grafico">
        <PanelPrecio ticker="GGAL" temporalidad="D" moneda={moneda} />
      </main>
    </div>
  )
}

export default App
