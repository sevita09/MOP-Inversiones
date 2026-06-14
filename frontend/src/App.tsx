import { Route, Routes } from 'react-router-dom'
import BuscadorTickers from './componentes/BuscadorTickers'
import EstadoBackend from './componentes/EstadoBackend'
import Navegacion from './componentes/Navegacion'
import Sidebar from './componentes/Sidebar'
import PaginaGrafico from './paginas/PaginaGrafico'
import PaginaCartera from './paginas/PaginaCartera'
import PaginaDatos from './paginas/PaginaDatos'

function App() {
  return (
    <div className="app">
      <header className="encabezado">
        <img src="/logo.png" alt="MOP Inversiones" className="logo-encabezado" />
        <span className="titulo-encabezado">MOP - Inversiones</span>
        <EstadoBackend />
        <Navegacion />
      </header>
      <div className="cuerpo">
        <div className="contenido">
          <Routes>
            <Route path="/" element={<PaginaGrafico />} />
            <Route path="/cartera" element={<PaginaCartera />} />
            <Route path="/datos" element={<PaginaDatos />} />
          </Routes>
        </div>
        <Sidebar />
      </div>
      <BuscadorTickers />
    </div>
  )
}

export default App
