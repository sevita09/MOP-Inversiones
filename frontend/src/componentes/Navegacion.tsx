import { NavLink } from 'react-router-dom'
import { usarSenalesSinVer } from '../hooks/usarSenales'
import './Navegacion.css'

const SECCIONES = [
  { ruta: '/', etiqueta: 'Gráfico' },
  { ruta: '/bots', etiqueta: 'Bots' },
  { ruta: '/senales', etiqueta: 'Señales' },
  { ruta: '/cartera', etiqueta: 'Cartera' },
  { ruta: '/datos', etiqueta: 'Datos' },
]

function Navegacion() {
  const sinVer = usarSenalesSinVer()

  return (
    <nav className="navegacion">
      {SECCIONES.map(({ ruta, etiqueta }) => (
        <NavLink
          key={ruta}
          to={ruta}
          end={ruta === '/'}
          className={({ isActive }) => `tab-navegacion${isActive ? ' activo' : ''}`}
        >
          {etiqueta}
          {ruta === '/senales' && sinVer > 0 && <span className="badge-nav">{sinVer}</span>}
        </NavLink>
      ))}
    </nav>
  )
}

export default Navegacion
