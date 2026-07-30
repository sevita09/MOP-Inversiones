import { useMemo, useState } from 'react'
import LogoTicker from '../LogoTicker'
import DetalleEscenarios from './DetalleEscenarios'
import { usarEscenariosDeVenta, usarVentasCerradas } from '../../hooks/usarEscenarios'
import './PanelWhatIf.css'

const pesos = (valor: number) => valor.toLocaleString('es-AR', { maximumFractionDigits: 2 })
const signo = (valor: number) => (valor > 0 ? '+' : '')

// Filas por página: con años de historia el listado puede tener cientos
const POR_PAGINA = 10

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

/** ¿Qué pasaba si vendía antes o después? Escenarios sobre cada venta cerrada. */
function PanelWhatIf() {
  const { ventas, captura, cargando } = usarVentasCerradas()
  const [papel, setPapel] = useState('')
  const [pagina, setPagina] = useState(0)
  const [elegida, setElegida] = useState<number | null>(null)

  const papeles = useMemo(
    () => [...new Set(ventas.map((v) => v.ticker))].sort(),
    [ventas],
  )
  const filtradas = papel ? ventas.filter((v) => v.ticker === papel) : ventas
  const paginas = Math.max(1, Math.ceil(filtradas.length / POR_PAGINA))
  const desde = pagina * POR_PAGINA
  const enPagina = filtradas.slice(desde, desde + POR_PAGINA)
  const seleccionada = elegida ?? filtradas[0]?.id ?? null
  const detalle = usarEscenariosDeVenta(seleccionada)

  if (cargando) return <p className="whatif-cargando">Buscando ventas cerradas…</p>
  if (ventas.length === 0) {
    return (
      <p className="whatif-vacio">
        Todavía no hay ventas para analizar. El what-if compara cada venta cerrada contra las
        fechas en que podrías haber salido.
      </p>
    )
  }

  return (
    <div className="whatif">
      {captura !== null && captura.promedio_pct !== null && (
        <div className="captura-recorrido">
          <div className="dato-captura">
            <span title="Del recorrido que dio el papel mientras lo tuviste, cuánto te llevaste">
              Captura del recorrido
            </span>
            <strong>{captura.promedio_pct.toFixed(0)}%</strong>
            <span className="detalle-captura">
              promedio de {captura.medidas} {captura.medidas === 1 ? 'venta' : 'ventas'}
            </span>
          </div>
          <p className="nota-captura">
            Del recorrido que dio el papel <strong>mientras se lo tuvo</strong>: salir en ese techo
            es 100%, salir al costo es 0% y por debajo de 0% se salió perdiendo sobre una posición
            que había estado en ganancia. Una captura baja con resultado positivo dice que las
            tesis funcionaron y las salidas fueron tempranas.
          </p>
        </div>
      )}

      <div className="filtro-whatif">
        <label>
          Papel
          <select
            value={papel}
            onChange={(evento) => {
              setPapel(evento.target.value)
              setPagina(0)
              setElegida(null)
            }}
          >
            <option value="">todos</option>
            {papeles.map((t) => (
              <option key={t} value={t}>
                {t}
              </option>
            ))}
          </select>
        </label>
        <span className="conteo-whatif">
          {filtradas.length} {filtradas.length === 1 ? 'venta' : 'ventas'}
        </span>
      </div>

      <div className="tabla-ventas-contenedor">
        <table className="tabla-ventas">
          <thead>
            <tr>
              <th>Papel</th>
              <th title="La compra que consumió esta venta por FIFO">Compra</th>
              <th>Venta</th>
              <th>Papeles</th>
              <th>Resultado</th>
              <th>Resultado %</th>
            </tr>
          </thead>
          <tbody>
            {enPagina.map((venta) => (
              <tr
                key={venta.id}
                className={venta.id === seleccionada ? 'fila-elegida' : ''}
                onClick={() => setElegida(venta.id)}
              >
                <td>
                  <span className="papel-whatif">
                    <LogoTicker ticker={venta.ticker} tamano={16} />
                    {venta.ticker}
                  </span>
                </td>
                <td className="compra-fila">{fecha(venta.desde)}</td>
                <td>{fecha(venta.fecha)}</td>
                <td className="numero">{pesos(venta.cantidad)}</td>
                <td className={`numero resultado${clase(venta.pnl)}`}>
                  {signo(venta.pnl)}${pesos(venta.pnl)}
                </td>
                <td className={`numero resultado${clase(venta.pnl_pct)}`}>
                  {porcentaje(venta.pnl_pct)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {paginas > 1 && (
        <div className="paginado-whatif">
          <button
            type="button"
            onClick={() => setPagina(0)}
            disabled={pagina === 0}
            title="Primera página"
          >
            «
          </button>
          <button
            type="button"
            onClick={() => setPagina((n) => Math.max(0, n - 1))}
            disabled={pagina === 0}
          >
            ‹ Anterior
          </button>
          <span className="posicion-pagina">
            {desde + 1}–{Math.min(desde + POR_PAGINA, filtradas.length)} de {filtradas.length}
          </span>
          <button
            type="button"
            onClick={() => setPagina((n) => Math.min(paginas - 1, n + 1))}
            disabled={pagina >= paginas - 1}
          >
            Siguiente ›
          </button>
          <button
            type="button"
            onClick={() => setPagina(paginas - 1)}
            disabled={pagina >= paginas - 1}
            title="Última página"
          >
            »
          </button>
        </div>
      )}

      {detalle ? (
        <DetalleEscenarios venta={detalle} />
      ) : (
        <p className="whatif-cargando">Armando escenarios de la venta…</p>
      )}

      <p className="nota-whatif">
        Los escenarios mueven <strong>solo la fecha de salida</strong>: los papeles y las compras
        que consumió el FIFO quedan fijos, así la comparación aísla la decisión de cuándo vender.
        Los gastos de la venta hipotética se recalculan con las tasas del broker. Ojo con la
        diferencia entre las dos medidas: <strong>en el máximo</strong> busca el mejor precio de
        toda la historia del papel —incluso posterior a la venta—, mientras la captura de arriba
        solo mira el recorrido que hubo mientras la posición estaba abierta.
      </p>
    </div>
  )
}

export default PanelWhatIf
