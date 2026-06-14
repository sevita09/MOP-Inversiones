import type { Vela } from '../../api/tipos'

interface Props {
  vela: Vela
  velaPrevia: Vela | null
}

function formatearPrecio(valor: number): string {
  return valor.toLocaleString('es-AR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

function formatearVolumen(valor: number): string {
  if (valor >= 1_000_000) return `${(valor / 1_000_000).toFixed(1)}M`
  if (valor >= 1_000) return `${(valor / 1_000).toFixed(1)}K`
  return `${valor}`
}

function LeyendaOHLC({ vela, velaPrevia }: Props) {
  // Variación contra el cierre anterior (estilo TradingView); si no hay, contra la apertura
  const base = velaPrevia ? velaPrevia.cierre : vela.apertura
  const cambio = vela.cierre - base
  const cambioPct = base !== 0 ? (cambio / base) * 100 : 0
  const positivo = cambio >= 0
  const claseColor = positivo ? 'leyenda-verde' : 'leyenda-roja'
  const signo = positivo ? '+' : ''

  return (
    <div className="leyenda-ohlc">
      <span className="leyenda-campo">O <b>{formatearPrecio(vela.apertura)}</b></span>
      <span className="leyenda-campo">H <b>{formatearPrecio(vela.maximo)}</b></span>
      <span className="leyenda-campo">L <b>{formatearPrecio(vela.minimo)}</b></span>
      <span className="leyenda-campo">C <b>{formatearPrecio(vela.cierre)}</b></span>
      <span className={`leyenda-cambio ${claseColor}`}>
        {signo}{formatearPrecio(cambio)} ({signo}{cambioPct.toFixed(2)}%)
      </span>
      <span className="leyenda-campo">Vol <b>{formatearVolumen(vela.volumen)}</b></span>
    </div>
  )
}

export default LeyendaOHLC
