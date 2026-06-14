import LogoTicker from './LogoTicker'
import type { Precio } from '../api/tipos'

interface Props {
  simbolo: string
  precio: Precio | undefined
  activo: boolean
  favorito: boolean
  alElegir: (simbolo: string) => void
  alAlternarFavorito: (simbolo: string) => void
}

function formatearVariacion(pct: number): string {
  return `${pct >= 0 ? '+' : ''}${pct.toFixed(2)}%`
}

function FilaTicker({ simbolo, precio, activo, favorito, alElegir, alAlternarFavorito }: Props) {
  const variacion = precio && precio.variacion_pct !== null ? precio.variacion_pct : null

  return (
    <div className={`fila-ticker${activo ? ' activo' : ''}`}>
      <button
        type="button"
        className={`estrella${favorito ? ' marcada' : ''}`}
        title={favorito ? 'Quitar de favoritos' : 'Agregar a favoritos'}
        onClick={() => alAlternarFavorito(simbolo)}
      >
        {favorito ? '★' : '☆'}
      </button>
      <button type="button" className="fila-seleccion" onClick={() => alElegir(simbolo)}>
        <LogoTicker ticker={simbolo} tamano={18} />
        <span className="ticker-simbolo">{simbolo}</span>
        {variacion !== null && (
          <span className={`ticker-variacion ${variacion >= 0 ? 'var-verde' : 'var-roja'}`}>
            {formatearVariacion(variacion)}
          </span>
        )}
      </button>
    </div>
  )
}

export default FilaTicker
