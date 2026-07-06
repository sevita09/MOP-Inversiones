import { usarEstadoBackend } from '../hooks/usarEstadoBackend'
import { usarEstadoSync } from '../hooks/usarEstadoSync'
import { usarVersion } from '../hooks/usarVersion'
import './EstadoBackend.css'

function formatearMomento(iso: string): string {
  return new Date(iso).toLocaleString('es-AR', {
    day: '2-digit',
    month: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  })
}

/** Estado en el header: versión + punto de conexión + última actualización. */
function EstadoBackend() {
  const conexion = usarEstadoBackend()
  const { version } = usarVersion()
  const { enCurso, ultimaSync } = usarEstadoSync()

  if (conexion === 'sin_conexion') {
    return (
      <span className="estado-backend estado-sin_conexion">
        <span className="punto" />
        Backend no conectado
      </span>
    )
  }

  return (
    <span className={`estado-backend estado-${conexion}`}>
      {version && <span className="version-app">v{version}</span>}
      <span className="punto" title={conexion === 'conectado' ? 'Backend conectado' : 'Verificando…'} />
      {enCurso ? (
        <span className="ultima-sync">sincronizando…</span>
      ) : (
        ultimaSync && (
          <span className="ultima-sync" title="Última actualización de datos">
            Últ. act.: {formatearMomento(ultimaSync)}
          </span>
        )
      )}
    </span>
  )
}

export default EstadoBackend
