import type { Vela } from '../../api/tipos'
import { usarEstilos, conOpacidad } from '../../contextos/EstilosContext'
import { REC_EMA, REC_BANDAS, OPACIDAD_SIGMA } from './config/estilosIndicadores'

export interface ValoresBandas {
  inf1: number | null
  sup1: number | null
  inf2: number | null
  sup2: number | null
  inf3: number | null
  sup3: number | null
}

export interface ValoresBollinger {
  inferior: number | null
  media: number | null
  superior: number | null
}

export interface ValorEmaExtra {
  id: string
  etiqueta: string
  color: string
  valor: number | null
}

interface Props {
  vela: Vela
  velaPrevia: Vela | null
  // Posición del precio respecto a la EMA central, en σ (null = bandas apagadas)
  z: number | null
  ema: number | null // valor de la EMA central bajo el crosshair (null = EMA apagada)
  bandas: ValoresBandas | null // las 6 bandas σ (null = σ apagadas)
  bollinger: ValoresBollinger | null // banda inferior/media/superior de Bollinger
  emasExtra: ValorEmaExtra[] // EMAs extra del usuario (vacío = ninguna o EMA apagada)
  // Con ADR visible hay que dejarle su espacio arriba a la derecha
  conAdr?: boolean
}

function formatearPrecio(valor: number | null): string {
  if (valor == null) return '—'
  return valor.toLocaleString('es-AR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

function formatearVolumen(valor: number): string {
  if (valor >= 1_000_000) return `${(valor / 1_000_000).toFixed(1)}M`
  if (valor >= 1_000) return `${(valor / 1_000).toFixed(1)}K`
  return `${valor}`
}

// Semáforo de reversión por zona de σ: blanco dentro de ±1σ, amarillo entre 1 y
// 2σ, verde si está ≤ −2σ (barato) y rojo si está ≥ +2σ (caro).
function claseZ(z: number): string {
  const abs = Math.abs(z)
  if (abs <= 1) return 'z-neutro'
  if (abs < 2) return 'z-medio'
  return z >= 0 ? 'z-alto' : 'z-bajo'
}

function LeyendaOHLC({ vela, velaPrevia, z, ema, bandas, bollinger, emasExtra , conAdr}: Props) {
  // Colores efectivos (para que la leyenda coincida con las líneas del gráfico)
  const { estiloDe } = usarEstilos()
  const colorEma = estiloDe('ema', REC_EMA).color
  const colorBandas = estiloDe('bandas', REC_BANDAS).color ?? '#388bfd'

  // Variación contra el cierre anterior (estilo TradingView); si no hay, contra la apertura
  const base = velaPrevia ? velaPrevia.cierre : vela.apertura
  const cambio = vela.cierre - base
  const cambioPct = base !== 0 ? (cambio / base) * 100 : 0
  const positivo = cambio >= 0
  const claseColor = positivo ? 'leyenda-verde' : 'leyenda-roja'
  const signo = positivo ? '+' : ''

  const sigmas: { nivel: 1 | 2 | 3; inf: number | null; sup: number | null }[] = bandas
    ? [
        { nivel: 1, inf: bandas.inf1, sup: bandas.sup1 },
        { nivel: 2, inf: bandas.inf2, sup: bandas.sup2 },
        { nivel: 3, inf: bandas.inf3, sup: bandas.sup3 },
      ]
    : []

  return (
    <div className={`leyenda-ohlc${conAdr ? ' con-adr' : ''}`}>
      <span className="leyenda-campo">O <b>{formatearPrecio(vela.apertura)}</b></span>
      <span className="leyenda-campo">H <b>{formatearPrecio(vela.maximo)}</b></span>
      <span className="leyenda-campo">L <b>{formatearPrecio(vela.minimo)}</b></span>
      <span className="leyenda-campo">C <b>{formatearPrecio(vela.cierre)}</b></span>
      <span className={`leyenda-cambio ${claseColor}`}>
        {signo}{formatearPrecio(cambio)} ({signo}{cambioPct.toFixed(2)}%)
      </span>
      <span className="leyenda-campo">Vol <b>{formatearVolumen(vela.volumen)}</b></span>
      {ema !== null && (
        <span className="leyenda-campo">
          EMA <b style={{ color: colorEma }}>{formatearPrecio(ema)}</b>
        </span>
      )}
      {emasExtra.map((e) => (
        <span className="leyenda-campo" key={e.id}>
          {e.etiqueta} <b style={{ color: e.color }}>{formatearPrecio(e.valor)}</b>
        </span>
      ))}
      {z !== null && (
        <span className="leyenda-campo leyenda-z">
          Z: <b className={claseZ(z)}>{z >= 0 ? '+' : '−'}{Math.abs(z).toFixed(2)} σ</b>
        </span>
      )}
      {sigmas.map(({ nivel, inf, sup }) => (
        <span
          className="leyenda-campo"
          key={nivel}
          style={{ color: conOpacidad(colorBandas, OPACIDAD_SIGMA[nivel]) }}
        >
          {nivel}σ <b>{formatearPrecio(inf)}·{formatearPrecio(sup)}</b>
        </span>
      ))}
      {bollinger && (
        <span className="leyenda-campo leyenda-bollinger">
          BB <b>{formatearPrecio(bollinger.inferior)}·{formatearPrecio(bollinger.media)}·
          {formatearPrecio(bollinger.superior)}</b>
        </span>
      )}
    </div>
  )
}

export default LeyendaOHLC
