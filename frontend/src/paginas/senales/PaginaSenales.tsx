import { useEffect } from 'react'
import { usarSenales } from '../../hooks/usarSenales'
import FilaSenal from './FilaSenal'
import './PaginaSenales.css'

function PaginaSenales() {
  const { senales, cargando, marcarVistas, eliminar, eliminarVencidas } = usarSenales()
  const vencidas = senales.filter((s) => s.vigente === false).length

  // Al entrar a la página, las señales dejan de estar "sin ver" (apaga el badge)
  useEffect(() => {
    void marcarVistas()
  }, [marcarVistas])

  if (!cargando && senales.length === 0) {
    return (
      <div className="pagina-vacia">
        <img src="/sv-logo.png" alt="" className="logo-fondo" />
        <div className="senales-vacio-texto">
          <p className="senales-vacio-titulo">Todavía no hay señales.</p>
          <p>
            Creá un bot activo con reglas de entrada: cuando su última barra las cumpla,
            la señal aparece acá.
          </p>
        </div>
      </div>
    )
  }

  return (
    <div className="pagina-senales">
      <div className="cabecera-senales">
        <h2>Señales</h2>
        <span className="nota-senales">
          Los bots activos evalúan su última barra tras cada sincronización.
        </span>
        {vencidas > 0 && (
          <button
            type="button"
            className="boton-limpiar-vencidas"
            onClick={() => void eliminarVencidas()}
          >
            Eliminar {vencidas} que ya no se cumplen
          </button>
        )}
      </div>

      {cargando && <p className="senales-vacio">Cargando…</p>}

      <ul className="lista-senales">
        {senales.map((senal) => (
          <FilaSenal key={senal.id} senal={senal} alEliminar={() => void eliminar(senal.id)} />
        ))}
      </ul>
    </div>
  )
}

export default PaginaSenales
