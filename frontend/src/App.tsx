import EstadoBackend from './componentes/EstadoBackend'
import InterruptorMoneda from './componentes/InterruptorMoneda'

function App() {
  return (
    <div className="app">
      <header className="encabezado">
        <img src="/logo.png" alt="MOP Inversiones" className="logo-encabezado" />
        <span className="titulo-encabezado">MOP - Inversiones</span>
        <EstadoBackend />
        <InterruptorMoneda />
      </header>
      <main className="pantalla-principal">
        <img src="/sv-logo.png" alt="" className="logo-fondo" />
      </main>
    </div>
  )
}

export default App
