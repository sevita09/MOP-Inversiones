import { Route, Routes } from 'react-router-dom'
import AvisoActualizacion from './componentes/AvisoActualizacion'
import BuscadorTickers from './componentes/BuscadorTickers'
import EstadoBackend from './componentes/EstadoBackend'
import Navegacion from './componentes/Navegacion'
import Sidebar from './componentes/Sidebar'
import PaginaGrafico from './paginas/PaginaGrafico'
import PaginaBots from './paginas/bots/PaginaBots'
import PaginaBacktest from './paginas/backtest/PaginaBacktest'
import PaginaSenales from './paginas/senales/PaginaSenales'
import PaginaCartera from './paginas/cartera/PaginaCartera'
import PaginaEstacionalidad from './paginas/analisis/PaginaEstacionalidad'
import PaginaDatos from './paginas/PaginaDatos'
import { usarVersion } from './hooks/usarVersion'

function App() {
  const esDev = usarVersion().canal === 'dev'

  return (
    <div className="app">
      <header className="encabezado">
        <img
          src={esDev ? '/logo-dev.png' : '/logo.png'}
          alt="MOP Inversiones"
          className="logo-encabezado"
        />
        <span className="titulo-encabezado">
          MOP - Inversiones{esDev && <span className="chip-dev">DEV</span>}
        </span>
        <EstadoBackend />
        <AvisoActualizacion />
        <Navegacion />
      </header>
      <div className="cuerpo">
        <div className="contenido">
          <Routes>
            <Route path="/" element={<PaginaGrafico />} />
            <Route path="/bots" element={<PaginaBots />} />
            <Route path="/bots/:id/backtest" element={<PaginaBacktest />} />
            <Route path="/senales" element={<PaginaSenales />} />
            <Route path="/cartera" element={<PaginaCartera />} />
            <Route path="/estacionalidad" element={<PaginaEstacionalidad />} />
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
