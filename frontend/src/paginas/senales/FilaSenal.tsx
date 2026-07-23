import type { Senal } from '../../api/tipos'
import LogoTicker from '../../componentes/LogoTicker'
import { describirCondicion } from './describirCondicion'

const NOMBRE_TEMPORALIDAD: Record<string, string> = { D: 'Diario', S: 'Semanal', M: 'Mensual' }

function fechaBarra(ts: number): string {
  return new Date(ts * 1000).toLocaleDateString('es-AR', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
  })
}

function esDeHoy(creado: string): boolean {
  // `creado` viene como 'AAAA-MM-DD HH:MM:SS' en UTC (datetime('now') de SQLite)
  const fecha = new Date(creado.replace(' ', 'T') + 'Z')
  return fecha.toDateString() === new Date().toDateString()
}

interface Props {
  senal: Senal
  alEliminar: () => void
}

/** Una señal con su bot, el desglose de por qué disparó y si sigue vigente. */
function FilaSenal({ senal, alEliminar }: Props) {
  const { detalle } = senal
  const condiciones = detalle.condiciones ?? []

  return (
    <li className={`fila-senal${senal.vista ? '' : ' sin-ver'}${senal.vigente === false ? ' vencida' : ''}`}>
      <div className="encabezado-senal">
        <LogoTicker ticker={senal.ticker} tamano={26} />
        <div className="datos-senal">
          <span className="titulo-senal">
            <strong>{senal.ticker}</strong> — señal de entrada
            {esDeHoy(senal.creado) && <span className="chip-hoy">hoy</span>}
          </span>
          <span className="detalle-senal">
            Bot <strong>{detalle.bot ?? '—'}</strong> ·{' '}
            {NOMBRE_TEMPORALIDAD[detalle.temporalidad ?? ''] ?? ''} · barra del{' '}
            {fechaBarra(senal.ts_barra)}
            {detalle.cierre != null &&
              ` · cierre ${detalle.cierre.toLocaleString('es-AR', { maximumFractionDigits: 2 })} ${detalle.moneda ?? ''}`}
          </span>
        </div>
        <button type="button" className="eliminar-senal" title="Eliminar señal" onClick={alEliminar}>
          ×
        </button>
      </div>

      {condiciones.length > 0 && (
        <div className="porque-senal">
          <span className="titulo-porque">Por qué se disparó</span>
          <ul className="condiciones-senal">
            {condiciones.map((condicion, i) => {
              const d = describirCondicion(condicion)
              return (
                <li key={i} className={d.cumple ? 'cumple' : 'no-cumple'}>
                  <span className="tilde-condicion">{d.cumple ? '✓' : '·'}</span>
                  <span>
                    {d.sujeto} = <strong>{d.valor}</strong> — {d.relacion}
                  </span>
                </li>
              )
            })}
          </ul>
        </div>
      )}

      {senal.vigente === false && (
        <p className="aviso-vencida">
          ⚠ La entrada ya no se cumple en la última barra: la oportunidad se cerró o cambió.
        </p>
      )}
    </li>
  )
}

export default FilaSenal
