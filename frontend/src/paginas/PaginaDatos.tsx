import type { ReactNode } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import PaginaCorrelaciones from './analisis/PaginaCorrelaciones'
import PaginaEstacionalidad from './analisis/PaginaEstacionalidad'
import PaginaRatios from './analisis/PaginaRatios'
import './PaginaDatos.css'

type Vista = 'estacionalidad' | 'correlaciones' | 'ratios'

/** Cada análisis con su ícono: el cuadrito de la estacionalidad, la matriz de
 *  las correlaciones y la línea que sube y baja del ratio. */
const SECCIONES: { clave: Vista; etiqueta: string; detalle: string; icono: ReactNode }[] = [
  {
    clave: 'estacionalidad',
    etiqueta: 'Estacionalidad',
    detalle: '¿Hay meses que rinden distinto?',
    icono: (
      <svg viewBox="0 0 24 24" aria-hidden="true">
        <rect x="3" y="4" width="6" height="6" rx="1" />
        <rect x="10" y="4" width="6" height="6" rx="1" className="tenue" />
        <rect x="17" y="4" width="4" height="6" rx="1" />
        <rect x="3" y="11" width="6" height="6" rx="1" className="tenue" />
        <rect x="10" y="11" width="6" height="6" rx="1" />
        <rect x="17" y="11" width="4" height="6" rx="1" className="tenue" />
      </svg>
    ),
  },
  {
    clave: 'correlaciones',
    etiqueta: 'Correlaciones',
    detalle: '¿Qué papeles se mueven juntos?',
    icono: (
      <svg viewBox="0 0 24 24" aria-hidden="true">
        <rect x="3" y="3" width="5" height="5" rx="1" />
        <rect x="10" y="3" width="5" height="5" rx="1" className="tenue" />
        <rect x="17" y="3" width="4" height="5" rx="1" className="tenue" />
        <rect x="3" y="10" width="5" height="5" rx="1" className="tenue" />
        <rect x="10" y="10" width="5" height="5" rx="1" />
        <rect x="17" y="10" width="4" height="5" rx="1" className="tenue" />
        <rect x="3" y="17" width="5" height="4" rx="1" className="tenue" />
        <rect x="10" y="17" width="5" height="4" rx="1" className="tenue" />
        <rect x="17" y="17" width="4" height="4" rx="1" />
      </svg>
    ),
  },
  {
    clave: 'ratios',
    etiqueta: 'Ratio',
    detalle: '¿Cómo cambió la relación de un par?',
    icono: (
      <svg viewBox="0 0 24 24" aria-hidden="true">
        <polyline points="3,17 8,11 13,14 21,5" className="trazo" />
        <circle cx="8" cy="11" r="1.6" />
        <circle cx="13" cy="14" r="1.6" />
      </svg>
    ),
  },
]

/** Entrada de la sección: qué análisis hay, agrupados por tipo de activo. */
function Portada() {
  return (
    <div className="portada-datos">
      <section className="columna-datos renta-fija">
        <h2>Renta fija</h2>
        <p className="bajada-columna">Bonos, letras y curvas de tasa.</p>
        <div className="proximamente">
          <img src="/sv-logo.png" alt="" />
          <span>Próximamente</span>
        </div>
      </section>

      <section className="columna-datos">
        <h2>Renta variable</h2>
        <p className="bajada-columna">Acciones, índices, CEDEARs y las referencias del mercado.</p>
        <div className="accesos-datos">
          {SECCIONES.map(({ clave, etiqueta, detalle, icono }) => (
            <Link key={clave} to={`/datos/${clave}`} className="acceso-analisis">
              <span className="icono-analisis">{icono}</span>
              <span className="texto-acceso">
                <strong>{etiqueta}</strong>
                <span>{detalle}</span>
              </span>
            </Link>
          ))}
        </div>
      </section>
    </div>
  )
}

/** Análisis transversal. La subsección vive en la URL (`/datos/ratios`) para
 *  poder guardarla y volver, en vez de perderse al recargar. */
function PaginaDatos() {
  const { seccion } = useParams<{ seccion: string }>()
  const navegar = useNavigate()
  const vista = SECCIONES.find((s) => s.clave === seccion)?.clave

  if (!vista) return <Portada />

  return (
    <div className="pagina-datos">
      <div className="barra-datos">
        <Link to="/datos" className="volver-datos" title="Ver todos los análisis">
          ← Renta variable
        </Link>
        <div className="subsecciones-datos">
          {SECCIONES.map(({ clave, etiqueta }) => (
            <button
              key={clave}
              type="button"
              className={vista === clave ? 'subseccion activa' : 'subseccion'}
              onClick={() => navegar(`/datos/${clave}`)}
            >
              {etiqueta}
            </button>
          ))}
        </div>
      </div>

      {vista === 'estacionalidad' && <PaginaEstacionalidad />}
      {vista === 'correlaciones' && <PaginaCorrelaciones />}
      {vista === 'ratios' && <PaginaRatios />}
    </div>
  )
}

export default PaginaDatos
