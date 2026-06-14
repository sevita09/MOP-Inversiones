import { usarEstadoBackend } from '../hooks/usarEstadoBackend'
import './EstadoBackend.css'

const TEXTOS = {
  verificando: 'Verificando backend…',
  conectado: 'Backend conectado',
  sin_conexion: 'Backend sin conexión',
} as const

function EstadoBackend() {
  const conexion = usarEstadoBackend()

  return (
    <span className={`estado-backend estado-${conexion}`}>
      <span className="punto" />
      {TEXTOS[conexion]}
    </span>
  )
}

export default EstadoBackend
