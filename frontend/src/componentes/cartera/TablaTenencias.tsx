import { useEffect, useState } from 'react'
import { obtenerTenencias } from '../../api/cliente'
import type { Tenencias } from '../../api/tipos'
import LogoTicker from '../LogoTicker'
import './TablaTenencias.css'

const pesos = (valor: number) => valor.toLocaleString('es-AR', { maximumFractionDigits: 2 })
const signo = (valor: number) => (valor > 0 ? '+' : '')

function fecha(texto: string): string {
  const [anio, mes, dia] = texto.split('-')
  return `${dia}/${mes}/${anio.slice(2)}`
}

/** Posiciones abiertas con su costo, valor de mercado y P&L no realizado. */
function TablaTenencias() {
  const [datos, setDatos] = useState<Tenencias | null>(null)
  const [cargando, setCargando] = useState(true)

  useEffect(() => {
    obtenerTenencias()
      .then(setDatos)
      .catch(() => setDatos(null))
      .finally(() => setCargando(false))
  }, [])

  if (cargando) return <p className="tenencias-cargando">Calculando tenencias…</p>
  if (!datos || datos.posiciones.length === 0) {
    return (
      <p className="tenencias-vacio">
        No hay posiciones abiertas. Cargá una compra en el historial y aparece acá.
      </p>
    )
  }

  const { posiciones, totales } = datos

  return (
    <div className="tenencias">
      <div className="resumen-cartera">
        <div className="dato-cartera">
          <span>Invertido</span>
          <strong>${pesos(totales.costo)}</strong>
        </div>
        <div className="dato-cartera">
          <span>Valor hoy</span>
          <strong>${pesos(totales.valor_actual)}</strong>
          {totales.valor_usd !== null && (
            <span className="usd-cartera">US${pesos(totales.valor_usd)}</span>
          )}
        </div>
        <div className={`dato-cartera resultado${totales.pnl >= 0 ? ' positivo' : ' negativo'}`}>
          <span>Resultado no realizado</span>
          <strong>
            {signo(totales.pnl)}${pesos(totales.pnl)}
            {totales.pnl_pct !== null && (
              <span className="pct-cartera">
                {' '}
                ({signo(totales.pnl_pct)}
                {totales.pnl_pct.toFixed(1)}%)
              </span>
            )}
          </strong>
          {totales.pnl_usd !== null && (
            <span className="usd-cartera">
              {signo(totales.pnl_usd)}US${pesos(totales.pnl_usd)}
            </span>
          )}
        </div>
      </div>

      <div className="tabla-tenencias-contenedor">
        <table className="tabla-tenencias">
          <thead>
            <tr>
              <th>Papel</th>
              <th>Cantidad</th>
              <th title="Lo que costó cada papel, con los gastos incluidos">Precio promedio</th>
              <th>Precio hoy</th>
              <th>Invertido</th>
              <th>Valor hoy</th>
              <th>Resultado</th>
              <th title="Porcentaje del valor de la cartera">Peso</th>
              <th title="Fecha de la compra más vieja que sigue abierta">Desde</th>
            </tr>
          </thead>
          <tbody>
            {posiciones.map((posicion) => (
              <tr key={posicion.ticker}>
                <td>
                  <span className="papel-tenencia">
                    <LogoTicker ticker={posicion.ticker} tamano={18} />
                    {posicion.ticker}
                  </span>
                </td>
                <td className="numero">{pesos(posicion.cantidad)}</td>
                <td className="numero">${pesos(posicion.precio_promedio)}</td>
                <td className="numero">
                  {posicion.precio_actual === null ? '—' : `$${pesos(posicion.precio_actual)}`}
                </td>
                <td className="numero">${pesos(posicion.costo)}</td>
                <td className="numero valor">
                  {posicion.valor_actual === null ? '—' : `$${pesos(posicion.valor_actual)}`}
                </td>
                <td
                  className={`numero resultado${
                    posicion.pnl === null ? '' : posicion.pnl >= 0 ? ' positivo' : ' negativo'
                  }`}
                >
                  {posicion.pnl === null ? (
                    '—'
                  ) : (
                    <>
                      {signo(posicion.pnl)}${pesos(posicion.pnl)}
                      {posicion.pnl_pct !== null && (
                        <span className="pct-fila">
                          {' '}
                          {signo(posicion.pnl_pct)}
                          {posicion.pnl_pct.toFixed(1)}%
                        </span>
                      )}
                    </>
                  )}
                </td>
                <td className="numero peso">
                  {posicion.peso_pct === null ? '—' : `${posicion.peso_pct.toFixed(1)}%`}
                </td>
                <td className="numero">{fecha(posicion.desde)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <p className="nota-tenencias">
        Costo por <strong>FIFO</strong>: al vender se consumen las compras más viejas, y los
        gastos del boleto están incluidos en el precio promedio.
        {totales.tasa_ccl !== null && ` Dólares al CCL de $${pesos(totales.tasa_ccl)}.`}
      </p>
    </div>
  )
}

export default TablaTenencias
