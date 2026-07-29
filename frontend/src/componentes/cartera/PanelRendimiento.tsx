import { useState } from 'react'
import type { Moneda, Realizado, Rendimiento } from '../../api/tipos'
import LogoTicker from '../LogoTicker'
import AyudaRendimiento from './AyudaRendimiento'
import CurvaRendimiento from './CurvaRendimiento'
import { usarRendimiento } from '../../hooks/usarRendimiento'
import './PanelRendimiento.css'

const pesos = (valor: number) => valor.toLocaleString('es-AR', { maximumFractionDigits: 2 })
const signo = (valor: number) => (valor > 0 ? '+' : '')

function porcentaje(valor: number | null): string {
  return valor === null ? '—' : `${signo(valor)}${valor.toFixed(1)}%`
}

function clase(valor: number | null): string {
  if (valor === null) return ''
  return valor >= 0 ? ' positivo' : ' negativo'
}

function fecha(texto: string): string {
  const [anio, mes, dia] = texto.split('-')
  return `${dia}/${mes}/${anio.slice(2)}`
}

/** Importe en dólares, o un guión si falta el MEP de alguna punta. */
function dolares(valor: number | null): string {
  return valor === null ? '—' : `${signo(valor)}US$${pesos(valor)}`
}

/** Contra qué se compara la cartera en cada moneda, y cómo se lee el detalle. */
const COMPARACIONES: Record<string, { titulo: string; detalle: (pct: string) => string }> = {
  mercado: { titulo: 'vs MERVAL', detalle: (p) => `el mercado hizo ${p}` },
  inflacion: { titulo: 'vs Inflación', detalle: (p) => `los precios subieron ${p}` },
  spy: { titulo: 'vs S&P', detalle: (p) => `el S&P hizo ${p}` },
  mep: { titulo: 'vs Dólar MEP', detalle: (p) => `el MEP subió ${p}` },
  brkb: { titulo: 'vs BRK.B', detalle: (p) => `Berkshire hizo ${p}` },
  btc: { titulo: 'vs BTC', detalle: (p) => `el bitcoin hizo ${p}` },
}

const TARJETAS_ARS = ['mercado', 'inflacion', 'spy', 'mep']
const TARJETAS_USD = ['mercado', 'brkb', 'spy', 'btc']

/** Tarjetas de arriba: cuánto rindió y contra qué se lo compara. */
function Resumen({ datos }: { datos: Rendimiento }) {
  const { totales, moneda } = datos
  const simbolo = moneda === 'USD' ? 'US$' : '$'
  const rotuloMoneda = moneda === 'USD' ? 'U$S' : '$'
  const claves = moneda === 'USD' ? TARJETAS_USD : TARJETAS_ARS

  return (
    <div className="resumen-rendimiento">
      <div className={`dato-rendimiento${clase(totales.twr_pct)}`}>
        <span className="rotulo-con-ayuda">
          <span title="Retorno ponderado por tiempo: no lo mueven los aportes ni los retiros">
            Rendimiento {rotuloMoneda} (TWR)
          </span>
          <AyudaRendimiento />
        </span>
        <strong>{porcentaje(totales.twr_pct)}</strong>
        <span className="detalle-rendimiento">
          {fecha(totales.desde)} → {fecha(totales.hasta)}
        </span>
      </div>

      {claves.map((clave) => {
        const { titulo, detalle } = COMPARACIONES[clave]
        const diferencia = totales.contra[clave] ?? null
        return (
          <div key={clave} className={`dato-rendimiento${clase(diferencia)}`}>
            <span>{titulo}</span>
            <strong>{porcentaje(diferencia)}</strong>
            <span className="detalle-rendimiento">
              {detalle(porcentaje(totales.variaciones[clave] ?? null))}
            </span>
          </div>
        )
      })}

      <div className="dato-rendimiento monto">
        <span title="Lo que valen hoy las posiciones abiertas, al último cierre">
          Valor actual de la cartera
        </span>
        <strong>
          {simbolo}
          {pesos(totales.valor_actual)}
        </strong>
        <span
          className={`detalle-rendimiento${clase(totales.ganancia)}`}
          title="Lo que quedó, menos lo que ya valía al empezar el período y lo aportado en el medio"
        >
          ganancia {signo(totales.ganancia)}
          {simbolo}
          {pesos(totales.ganancia)}
        </span>
      </div>
    </div>
  )
}

/** Lo ya cobrado, papel por papel. Va siempre en dólares: es el resultado que
 *  no se licúa, comparable entre operaciones de años distintos. */
function TablaRealizado({ datos }: { datos: Realizado }) {
  return (
    <>
      <h3 className="titulo-realizado">
        Resultado realizado
        <span className="nota-titulo">
          {datos.totales.operaciones} ventas · en dólares, con el MEP de cada punta
        </span>
      </h3>
      <div className="tabla-realizado-contenedor">
        <table className="tabla-realizado">
          <thead>
            <tr>
              <th>Papel</th>
              <th>Ventas</th>
              <th>Papeles</th>
              <th title="Lo que costaron esos papeles, con gastos, al MEP de cada compra">
                Costo US$
              </th>
              <th title="Lo que entró, neto de gastos, al MEP de la venta">Ingreso US$</th>
              <th>Resultado US$</th>
            </tr>
          </thead>
          <tbody>
            {datos.papeles.map((papel) => (
              <tr key={papel.ticker}>
                <td>
                  <span className="papel-realizado">
                    <LogoTicker ticker={papel.ticker} tamano={18} />
                    {papel.ticker}
                  </span>
                </td>
                <td className="numero">{papel.operaciones}</td>
                <td className="numero">{pesos(papel.cantidad)}</td>
                <td className="numero">
                  {papel.costo_usd === null ? '—' : `US$${pesos(papel.costo_usd)}`}
                </td>
                <td className="numero">
                  {papel.ingreso_usd === null ? '—' : `US$${pesos(papel.ingreso_usd)}`}
                </td>
                <td className={`numero resultado${clase(papel.pnl_usd)}`}>
                  {dolares(papel.pnl_usd)}
                  {papel.pnl_usd_pct !== null && (
                    <span className="pct-realizado"> {porcentaje(papel.pnl_usd_pct)}</span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
          <tfoot>
            <tr>
              <td colSpan={3}>Total</td>
              <td className="numero">
                {datos.totales.costo_usd === null ? '—' : `US$${pesos(datos.totales.costo_usd)}`}
              </td>
              <td className="numero">
                {datos.totales.ingreso_usd === null
                  ? '—'
                  : `US$${pesos(datos.totales.ingreso_usd)}`}
              </td>
              <td className={`numero resultado${clase(datos.totales.pnl_usd)}`}>
                {dolares(datos.totales.pnl_usd)}
                {datos.totales.pnl_usd_pct !== null && (
                  <span className="pct-realizado"> {porcentaje(datos.totales.pnl_usd_pct)}</span>
                )}
              </td>
            </tr>
          </tfoot>
        </table>
      </div>
    </>
  )
}

/** Rendimiento de la cartera: curva contra benchmarks y resultado ya realizado. */
function PanelRendimiento() {
  const [periodo, setPeriodo] = useState('Todo')
  const [moneda, setMoneda] = useState<Moneda>('ARS')
  const { rendimiento, realizado, cargando } = usarRendimiento(periodo, moneda)

  if (cargando) return <p className="rendimiento-cargando">Calculando rendimiento…</p>
  if (!rendimiento || rendimiento.fechas.length === 0) {
    return (
      <p className="rendimiento-vacio">
        Todavía no hay ruedas para medir. Cargá una compra y la curva aparece acá.
      </p>
    )
  }

  return (
    <div className="rendimiento">
      <Resumen datos={rendimiento} />
      <CurvaRendimiento
        datos={rendimiento}
        periodo={periodo}
        alCambiarPeriodo={setPeriodo}
        moneda={moneda}
        alCambiarMoneda={setMoneda}
      />

      {realizado && realizado.papeles.length > 0 && <TablaRealizado datos={realizado} />}

      <p className="nota-rendimiento-pie">
        El <strong>TWR</strong> mide el rendimiento de las decisiones: parte la historia en tramos
        entre aporte y aporte, así meter plata justo antes de una suba no infla el número. Los
        benchmarks arrancan en 100 la misma rueda que la cartera. La cartera se valúa con el
        <strong> dólar MEP</strong> (GGAL contra GGALD.BA).
      </p>
    </div>
  )
}

export default PanelRendimiento
