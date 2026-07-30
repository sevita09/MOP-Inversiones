import { useEffect, useState } from 'react'
import type { EscenariosDeVenta } from '../../api/tipos'
import { usarWhatIf } from '../../hooks/usarEscenarios'

const pesos = (valor: number) => valor.toLocaleString('es-AR', { maximumFractionDigits: 2 })
const signo = (valor: number) => (valor > 0 ? '+' : '')

function fecha(texto: string): string {
  const [anio, mes, dia] = texto.split('-')
  return `${dia}/${mes}/${anio.slice(2)}`
}

function clase(valor: number | null): string {
  if (valor === null) return ''
  return valor >= 0 ? ' positivo' : ' negativo'
}

function porcentaje(valor: number | null): string {
  return valor === null ? '—' : `${signo(valor)}${valor.toFixed(1)}%`
}

const UN_DIA = 86_400_000

/** 'AAAA-MM-DD' + n días, sin pasar por zonas horarias. */
function sumarDias(desde: string, dias: number): string {
  return new Date(Date.parse(`${desde}T00:00:00Z`) + dias * UN_DIA).toISOString().slice(0, 10)
}

function diasEntre(desde: string, hasta: string): number {
  return Math.round((Date.parse(`${hasta}T00:00:00Z`) - Date.parse(`${desde}T00:00:00Z`)) / UN_DIA)
}

interface Props {
  venta: EscenariosDeVenta
}

/** Escenarios automáticos de una venta y el slider de fecha alternativa. */
function DetalleEscenarios({ venta }: Props) {
  const total = venta.hasta ? diasEntre(venta.desde, venta.hasta) : 0
  const diaReal = diasEntre(venta.desde, venta.real.fecha)
  const [dia, setDia] = useState(diaReal)
  const { resultado, consultar } = usarWhatIf(venta.id)

  // Al cambiar de venta el slider vuelve a la fecha real de esa operación
  useEffect(() => {
    setDia(diaReal)
    consultar(venta.real.fecha)
  }, [venta.id, diaReal, venta.real.fecha, consultar])

  const mover = (valor: number) => {
    setDia(valor)
    consultar(sumarDias(venta.desde, valor))
  }

  const diferencia = resultado?.diferencia ?? 0

  return (
    <div className="detalle-escenarios">
      <div className="slider-escenario">
        <div className="cabecera-slider">
          <span>
            Vender el <strong>{fecha(sumarDias(venta.desde, dia))}</strong>
          </span>
          {resultado && (
            <span className="resultado-slider">
              <span className={`pnl-slider${clase(resultado.alternativo.pnl)}`}>
                {signo(resultado.alternativo.pnl)}${pesos(resultado.alternativo.pnl)}
              </span>
              <span className={`dif-slider${clase(diferencia)}`}>
                {signo(diferencia)}${pesos(diferencia)} vs lo que hice
              </span>
            </span>
          )}
        </div>
        <input
          type="range"
          min={0}
          max={total}
          value={dia}
          onChange={(evento) => mover(Number(evento.target.value))}
          className="rango-escenario"
          aria-label="Fecha alternativa de venta"
        />
        <div className="extremos-slider">
          <span>{fecha(venta.desde)} · compra</span>
          <button type="button" className="volver-real" onClick={() => mover(diaReal)}>
            ↺ mi venta ({fecha(venta.real.fecha)})
          </button>
          <span>{venta.hasta && `${fecha(venta.hasta)} · hoy`}</span>
        </div>
      </div>

      <div className="tabla-escenarios-contenedor">
        <table className="tabla-escenarios">
          <thead>
            <tr>
              <th>Escenario</th>
              <th>Fecha</th>
              <th>Precio</th>
              <th>Resultado</th>
              <th title="El resultado sobre el costo de esos papeles">Resultado %</th>
              <th title="Cuánto mejor o peor que la venta que hice">Diferencia</th>
              <th title="La diferencia en puntos porcentuales sobre el costo">Dif. %</th>
            </tr>
          </thead>
          <tbody>
            <tr className="fila-real">
              <td>lo que hice</td>
              <td>{fecha(venta.real.fecha)}</td>
              <td className="numero">${pesos(venta.real.precio)}</td>
              <td className={`numero resultado${clase(venta.real.pnl)}`}>
                {signo(venta.real.pnl)}${pesos(venta.real.pnl)}
              </td>
              <td className={`numero resultado${clase(venta.real.pnl_pct)}`}>
                {porcentaje(venta.real.pnl_pct)}
              </td>
              <td className="numero">—</td>
              <td className="numero">—</td>
            </tr>
            {venta.escenarios.map((escenario) => (
              <tr
                key={escenario.nombre}
                className={escenario.nombre === venta.mejor?.nombre ? 'fila-mejor' : ''}
              >
                <td>{escenario.nombre}</td>
                <td>{fecha(escenario.fecha)}</td>
                <td className="numero">${pesos(escenario.precio)}</td>
                <td className={`numero resultado${clase(escenario.pnl)}`}>
                  {signo(escenario.pnl)}${pesos(escenario.pnl)}
                </td>
                <td className={`numero resultado${clase(escenario.pnl_pct)}`}>
                  {porcentaje(escenario.pnl_pct)}
                </td>
                <td className={`numero resultado${clase(escenario.diferencia)}`}>
                  {signo(escenario.diferencia)}${pesos(escenario.diferencia)}
                </td>
                <td className={`numero resultado${clase(escenario.diferencia_pct)}`}>
                  {porcentaje(escenario.diferencia_pct)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

export default DetalleEscenarios
