import { NavLink } from 'react-router-dom'
import './Navegacion.css'

const SECCIONES = [
  { ruta: '/', etiqueta: 'Gráfico' },
  { ruta: '/cartera', etiqueta: 'Cartera' },
  { ruta: '/datos', etiqueta: 'Datos' },
]

function Navegacion() {
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
        </NavLink>
      ))}
    </nav>
  )
}

export default Navegacion
