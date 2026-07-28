import { useState } from 'react'
import type { Transaccion } from '../../api/tipos'
import LogoTicker from '../../componentes/LogoTicker'
import ConfigComisiones from '../../componentes/cartera/ConfigComisiones'
import PanelSplits from '../../componentes/cartera/PanelSplits'
import TablaTenencias from '../../componentes/cartera/TablaTenencias'
import FormularioOperacion from '../../componentes/cartera/FormularioOperacion'
import { usarTransacciones } from '../../hooks/usarTransacciones'
import './PaginaCartera.css'

function fecha(texto: string): string {
  // 'AAAA-MM-DD' sin pasar por Date: evita el corrimiento de zona horaria
  const [anio, mes, dia] = texto.split('-')
  return `${dia}/${mes}/${anio.slice(2)}`
}

function pesos(valor: number): string {
  return valor.toLocaleString('es-AR', { maximumFractionDigits: 2 })
}

function PaginaCartera() {
  const { transacciones, cargando, crear, editar, eliminar } = usarTransacciones()
  const [formulario, setFormulario] = useState<'nueva' | Transaccion | null>(null)
  const [borrando, setBorrando] = useState<Transaccion | null>(null)
  const [ajustes, setAjustes] = useState(false)
  const [vista, setVista] = useState<'tenencias' | 'historial'>('tenencias')
  const [splits, setSplits] = useState(false)
  // Cambia al registrar o borrar un split: fuerza recalcular las tenencias
  const [revisionSplits, setRevisionSplits] = useState(0)

  const vacio = !cargando && transacciones.length === 0

  return (
    <div className={vacio ? 'pagina-vacia' : 'pagina-cartera'}>
      {vacio ? (
        <>
          <img src="/sv-logo.png" alt="" className="logo-fondo" />
          <div className="cartera-vacia-texto">
            <p className="cartera-vacia-titulo">Todavía no cargaste operaciones.</p>
            <p>
              Registrá tus compras y ventas reales: el precio se sugiere solo desde la rueda
              de esa fecha.
            </p>
            <button type="button" className="boton-nueva-operacion" onClick={() => setFormulario('nueva')}>
              ＋ Registrar operación
            </button>
          </div>
        </>
      ) : (
        <>
          <div className="cabecera-cartera">
            <h2>Cartera</h2>
            <div className="pestanas-cartera">
              <button
                type="button"
                className={vista === 'tenencias' ? 'pestana-cartera activa' : 'pestana-cartera'}
                onClick={() => setVista('tenencias')}
              >
                Tenencias
              </button>
              <button
                type="button"
                className={vista === 'historial' ? 'pestana-cartera activa' : 'pestana-cartera'}
                onClick={() => setVista('historial')}
              >
                Historial ({transacciones.length})
              </button>
            </div>
            <button
              type="button"
              className="boton-ajustes-cartera"
              data-tooltip="Splits de acciones"
              onClick={() => setSplits(true)}
            >
              ⇅
            </button>
            <button
              type="button"
              className="boton-ajustes-cartera sin-margen"
              data-tooltip="Configurar los gastos del broker"
              onClick={() => setAjustes(true)}
            >
              ⚙
            </button>
            <button
              type="button"
              className="boton-nueva-operacion"
              onClick={() => setFormulario('nueva')}
            >
              ＋ Registrar operación
            </button>
          </div>

          {cargando && <p className="cartera-cargando">Cargando…</p>}

          {vista === 'tenencias' && (
            <TablaTenencias key={`${transacciones.length}-${revisionSplits}`} />
          )}

          {vista === 'historial' && (
          <div className="tabla-operaciones-contenedor">
            <table className="tabla-operaciones">
              <thead>
                <tr>
                  <th>Fecha</th>
                  <th>Tipo</th>
                  <th>Papel</th>
                  <th>Cantidad</th>
                  <th>Precio</th>
                  <th>Comisión</th>
                  <th>Total</th>
                  <th>USD</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {transacciones.map((operacion) => (
                  <tr key={operacion.id}>
                    <td>{fecha(operacion.fecha)}</td>
                    <td>
                      <span className={`chip-tipo ${operacion.tipo}`}>
                        {operacion.tipo === 'compra' ? 'Compra' : 'Venta'}
                      </span>
                    </td>
                    <td>
                      <span className="papel-operacion">
                        <LogoTicker ticker={operacion.ticker} tamano={18} />
                        {operacion.ticker}
                      </span>
                    </td>
                    <td className="numero">{pesos(operacion.cantidad)}</td>
                    <td className="numero">${pesos(operacion.precio)}</td>
                    <td className="numero comision">${pesos(operacion.comision)}</td>
                    <td className="numero total">${pesos(operacion.monto_final)}</td>
                    <td className="numero usd">
                      {operacion.monto_final_usd === null
                        ? '—'
                        : `US$${pesos(operacion.monto_final_usd)}`}
                    </td>
                    <td className="acciones-operacion">
                      <button
                        type="button"
                        data-tooltip="Editar operación"
                        onClick={() => setFormulario(operacion)}
                      >
                        ✎
                      </button>
                      <button
                        type="button"
                        data-tooltip="Borrar operación"
                        className="accion-borrar"
                        onClick={() => setBorrando(operacion)}
                      >
                        🗑
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          )}
        </>
      )}

      {ajustes && <ConfigComisiones alCerrar={() => setAjustes(false)} />}

      {splits && (
        <PanelSplits
          alCerrar={() => setSplits(false)}
          alCambiar={() => setRevisionSplits((n) => n + 1)}
        />
      )}

      {formulario && (
        <FormularioOperacion
          operacion={formulario === 'nueva' ? null : formulario}
          alGuardar={async (datos) => {
            if (formulario === 'nueva') await crear(datos)
            else await editar(formulario.id, datos)
            setFormulario(null)
          }}
          alCerrar={() => setFormulario(null)}
        />
      )}

      {borrando && (
        <div className="fondo-confirmar" onClick={() => setBorrando(null)}>
          <div className="dialogo-confirmar" onClick={(evento) => evento.stopPropagation()}>
            <p>
              ¿Borrar la {borrando.tipo} de <strong>{borrando.ticker}</strong> del{' '}
              {fecha(borrando.fecha)}?
            </p>
            <p className="nota-confirmar">Se recalculan las tenencias sin esta operación.</p>
            <div className="botones-confirmar">
              <button
                type="button"
                className="boton-borrar"
                onClick={() => {
                  void eliminar(borrando.id)
                  setBorrando(null)
                }}
              >
                Borrar
              </button>
              <button type="button" className="boton-cancelar" onClick={() => setBorrando(null)}>
                Cancelar
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default PaginaCartera
