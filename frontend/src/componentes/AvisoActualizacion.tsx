import { useState } from 'react'
import { instalarActualizacion } from '../api/cliente'
import { usarActualizacion } from '../hooks/usarActualizacion'
import './AvisoActualizacion.css'

type Fase = 'aviso' | 'confirmando' | 'instalando' | 'error'

/** Aviso en el header cuando hay una versión nueva: pregunta y se instala sola. */
function AvisoActualizacion() {
  const estado = usarActualizacion()
  const [fase, setFase] = useState<Fase>('aviso')
  const [oculto, setOculto] = useState(false)

  if (!estado?.hay_nueva || oculto) return null

  const instalar = () => {
    setFase('instalando')
    instalarActualizacion().catch(() => {
      // 409: modo desarrollo o release sin .dmg — queda el link como plan B
      setFase('error')
    })
  }

  if (fase === 'instalando') {
    return (
      <span className="aviso-actualizacion instalando">
        Instalando v{estado.ultima}… la app se reinicia sola
      </span>
    )
  }

  if (fase === 'confirmando') {
    return (
      <span className="aviso-actualizacion">
        ¿Instalar v{estado.ultima} ahora?
        <button className="boton-instalar" onClick={instalar}>Instalar</button>
        <button className="boton-despues" onClick={() => setFase('aviso')}>Después</button>
      </span>
    )
  }

  return (
    <span className="aviso-actualizacion">
      {fase === 'error' ? (
        <a href={estado.url_descarga} target="_blank" rel="noreferrer">
          No se pudo auto-instalar — descargar v{estado.ultima}
        </a>
      ) : (
        <button className="boton-aviso" onClick={() => setFase('confirmando')}>
          ⬆ Nueva versión v{estado.ultima}
        </button>
      )}
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
