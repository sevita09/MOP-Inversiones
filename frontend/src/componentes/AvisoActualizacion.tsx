import { useState } from 'react'
import { usarActualizacion } from '../hooks/usarActualizacion'
import './AvisoActualizacion.css'

/** Aviso en el header cuando hay una versión más nueva publicada en GitHub. */
function AvisoActualizacion() {
  const estado = usarActualizacion()
  const [oculto, setOculto] = useState(false)

  if (!estado?.hay_nueva || oculto) return null

  return (
    <span className="aviso-actualizacion">
      <a href={estado.url_descarga} target="_blank" rel="noreferrer">
        ⬆ Nueva versión v{estado.ultima}
      </a>
      <button
        className="cerrar-aviso"
        onClick={() => setOculto(true)}
        title="Ocultar hasta el próximo arranque"
      >
        ×
      </button>
    </span>
  )
}

export default AvisoActualizacion
