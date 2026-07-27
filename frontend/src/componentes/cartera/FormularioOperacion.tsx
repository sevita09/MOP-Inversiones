import { useEffect, useMemo, useRef, useState } from 'react'
import {
  obtenerPapelesEnCartera,
  obtenerPrecioSugerido,
  obtenerTasaVigente,
} from '../../api/cliente'
import type { TasaVigente, Transaccion, TransaccionNueva, TipoOperacion } from '../../api/tipos'
import InputNumero from '../bots/InputNumero'
import LogoTicker from '../LogoTicker'
import { usarTickers } from '../../hooks/usarTickers'
import './FormularioOperacion.css'

interface Props {
  operacion: Transaccion | null // null = alta
  alGuardar: (datos: TransaccionNueva) => Promise<void>
  alCerrar: () => void
}

type ModoCarga = 'monto_final' | 'precio'

const HOY = () => new Date().toISOString().slice(0, 10)
const pesos = (valor: number) => valor.toLocaleString('es-AR', { maximumFractionDigits: 2 })

/** Alta y edición de una operación real.
 *
 *  Por defecto se carga como llega el resumen del broker: cantidad + monto final
 *  cobrado. El precio de mercado y la comisión los despeja el backend con la
 *  tasa vigente (que detecta sola el intradía). El modo "precio unitario" queda
 *  para cuando se conoce el precio de la orden. */
function FormularioOperacion({ operacion, alGuardar, alCerrar }: Props) {
  const paneles = usarTickers()
  const [tipo, setTipo] = useState<TipoOperacion>(operacion?.tipo ?? 'compra')
  const [ticker, setTicker] = useState(operacion?.ticker ?? '')
  const [busqueda, setBusqueda] = useState('')
  const [fecha, setFecha] = useState(operacion?.fecha ?? HOY())
  const [cantidad, setCantidad] = useState<number | null>(operacion?.cantidad ?? null)
  const [modo, setModo] = useState<ModoCarga>('monto_final')
  const [precio, setPrecio] = useState<number | null>(operacion?.precio ?? null)
  const [montoFinal, setMontoFinal] = useState<number | null>(operacion?.monto_final ?? null)
  const [nota, setNota] = useState(operacion?.nota ?? '')
  const [sugerido, setSugerido] = useState<number | null>(null)
  const [tasa, setTasa] = useState<TasaVigente | null>(null)
  const [enCartera, setEnCartera] = useState<Record<string, number>>({})
  const [mensaje, setMensaje] = useState('')
  const [guardando, setGuardando] = useState(false)
  // Al editar, la primera carga no debe pisar el precio real que se pagó
  const esEdicionInicial = useRef(operacion !== null)

  // Qué papeles se tienen hoy: en venta solo se ofrecen esos
  useEffect(() => {
    obtenerPapelesEnCartera()
      .then(setEnCartera)
      .catch(() => setEnCartera({}))
  }, [])

  const cambiarTipo = (nuevo: TipoOperacion) => {
    setTipo(nuevo)
    // Pasar a venta con un papel que no se tiene: se limpia la selección
    if (nuevo === 'venta' && ticker && !(ticker in enCartera)) {
      const propio = operacion?.tipo === 'venta' && operacion.ticker === ticker
      if (!propio) {
        setTicker('')
        setCantidad(null)
      }
    }
  }

  // Al editar una venta, sus propios papeles siguen disponibles para esa operación
  const disponible = (simbolo: string) => {
    const base = enCartera[simbolo] ?? 0
    const propios =
      operacion && operacion.tipo === 'venta' && operacion.ticker === simbolo
        ? operacion.cantidad
        : 0
    return base + propios
  }

  const candidatos = useMemo(() => {
    if (!paneles) return []
    const todos =
      tipo === 'venta'
        ? Object.keys(enCartera)
        : [
            ...paneles.panel_lider,
            ...paneles.panel_general,
            ...paneles.cedears,
            ...paneles.indices,
            ...paneles.cripto,
          ]
    const consulta = busqueda.trim().toUpperCase()
    // En venta se listan todos los tenidos aunque no se haya escrito nada:
    // son pocos y es lo único vendible
    if (!consulta) return tipo === 'venta' ? todos.slice(0, 8) : []
    return todos.filter((simbolo) => simbolo.includes(consulta)).slice(0, 8)
  }, [paneles, busqueda, tipo, enCartera])

  // Cambiar ticker o fecha trae el cierre de esa rueda y actualiza el precio
  useEffect(() => {
    if (!ticker || !fecha) {
      setSugerido(null)
      return
    }
    let activo = true
    obtenerPrecioSugerido(ticker, fecha)
      .then(({ precio: cierre }) => {
        if (!activo) return
        setSugerido(cierre)
        if (esEdicionInicial.current) {
          esEdicionInicial.current = false // respetar lo guardado la primera vez
          return
        }
        setPrecio(cierre)
      })
      .catch(() => activo && setSugerido(null))
    return () => {
      activo = false
    }
  }, [ticker, fecha])

  // Qué comisión corresponde (avisa si detectó compra-venta en el día)
  useEffect(() => {
    if (!ticker || !fecha) {
      setTasa(null)
      return
    }
    let activo = true
    obtenerTasaVigente(ticker, fecha, tipo)
      .then((vigente) => activo && setTasa(vigente))
      .catch(() => activo && setTasa(null))
    return () => {
      activo = false
    }
  }, [ticker, fecha, tipo])

  // Vista previa con el mismo desglose del boleto del broker
  const previsualizacion = useMemo(() => {
    if (!cantidad || !tasa) return null
    const efectiva = tasa.tasa_efectiva_pct / 100
    const bruto =
      modo === 'monto_final'
        ? montoFinal
          ? montoFinal / (tipo === 'compra' ? 1 + efectiva : 1 - efectiva)
          : null
        : precio
          ? precio * cantidad
          : null
    if (bruto === null) return null

    const arancel = (bruto * tasa.arancel_aplicado_pct) / 100
    const derechos = (bruto * tasa.derechos_mercado_pct) / 100
    const iva = ((arancel + derechos) * tasa.iva_pct) / 100
    const gastos = arancel + derechos + iva
    return {
      precio: bruto / cantidad,
      bruto,
      arancel,
      derechos,
      iva,
      gastos,
      montoFinal: tipo === 'compra' ? bruto + gastos : bruto - gastos,
    }
  }, [cantidad, precio, montoFinal, modo, tipo, tasa])

  const guardar = async () => {
    if (!ticker) return setMensaje('Elegí un ticker')
    if (!cantidad || cantidad <= 0) return setMensaje('La cantidad debe ser mayor a 0')
    if (modo === 'monto_final' && !montoFinal) return setMensaje('Poné el monto que te cobró el broker')
    if (modo === 'precio' && !precio) return setMensaje('Poné el precio unitario')

    setGuardando(true)
    setMensaje('')
    try {
      await alGuardar({
        ticker,
        tipo,
        fecha,
        cantidad,
        ...(modo === 'monto_final' ? { monto_final: montoFinal! } : { precio: precio! }),
        nota: nota.trim(),
      })
    } catch {
      setMensaje('No se pudo guardar la operación')
      setGuardando(false)
    }
  }

  return (
    <div className="fondo-formulario-operacion" onClick={alCerrar}>
      <div className="formulario-operacion" onClick={(evento) => evento.stopPropagation()}>
        <div className="cabecera-formulario-operacion">
          <span>{operacion ? 'Editar operación' : 'Nueva operación'}</span>
          <button type="button" className="cerrar-formulario" onClick={alCerrar}>
            ×
          </button>
        </div>

        <div className="campo-operacion">
          <span>Tipo</span>
          <div className="chips-operacion">
            {(['compra', 'venta'] as TipoOperacion[]).map((valor) => (
              <button
                key={valor}
                type="button"
                className={`chip-operacion ${valor}${valor === tipo ? ' activo' : ''}`}
                onClick={() => cambiarTipo(valor)}
              >
                {valor === 'compra' ? 'Compra' : 'Venta'}
              </button>
            ))}
          </div>
        </div>

        <label className="campo-operacion">
          <span>Ticker</span>
          {ticker ? (
            <span className="ticker-elegido">
              <LogoTicker ticker={ticker} tamano={20} />
              {ticker}
              <button type="button" onClick={() => setTicker('')} title="Cambiar">
                ×
              </button>
            </span>
          ) : (
            <span className="buscador-ticker-operacion">
              <input
                autoFocus
                value={busqueda}
                placeholder="Buscar ticker…"
                onChange={(evento) => setBusqueda(evento.target.value.toUpperCase())}
              />
              {candidatos.length > 0 && (
                <ul className="sugerencias-ticker">
                  {candidatos.map((simbolo) => (
                    <li key={simbolo}>
                      <button
                        type="button"
                        onClick={() => {
                          setTicker(simbolo)
                          setBusqueda('')
                          // En venta se precarga todo lo que se tiene: lo normal
                          // es vender la posición entera, y si no se edita
                          if (tipo === 'venta') setCantidad(disponible(simbolo))
                        }}
                      >
                        <LogoTicker ticker={simbolo} tamano={18} />
                        {simbolo}
                        {tipo === 'venta' && (
                          <span className="cantidad-disponible">
                            {disponible(simbolo).toLocaleString('es-AR')}
                          </span>
                        )}
                      </button>
                    </li>
                  ))}
                </ul>
              )}
            </span>
          )}
        </label>

        <div className="fila-operacion">
          <label className="campo-operacion">
            <span>Fecha</span>
            <input type="date" value={fecha} onChange={(evento) => setFecha(evento.target.value)} />
          </label>
          <label className="campo-operacion">
            <span>Cantidad</span>
            <InputNumero valor={cantidad} miles placeholder="0" alCambiar={setCantidad} />
          </label>
        </div>

        {tipo === 'venta' && ticker && (
          <span
            className={`disponible-aviso${
              cantidad && cantidad > disponible(ticker) ? ' excede' : ''
            }`}
          >
            {cantidad && cantidad > disponible(ticker)
              ? `Tenés ${disponible(ticker).toLocaleString('es-AR')} papeles: estás vendiendo de más`
              : `En cartera: ${disponible(ticker).toLocaleString('es-AR')} papeles`}
          </span>
        )}

        <div className="campo-operacion">
          <span>Cargar por</span>
          <div className="chips-operacion">
            <button
              type="button"
              className={`chip-modo${modo === 'monto_final' ? ' activo' : ''}`}
              onClick={() => setModo('monto_final')}
            >
              Monto del broker
            </button>
            <button
              type="button"
              className={`chip-modo${modo === 'precio' ? ' activo' : ''}`}
              onClick={() => setModo('precio')}
            >
              Precio unitario
            </button>
          </div>
        </div>

        {modo === 'monto_final' ? (
          <label className="campo-operacion">
            <span>{tipo === 'compra' ? 'Monto total pagado' : 'Monto total cobrado'}</span>
            <InputNumero valor={montoFinal} prefijo="$" miles alCambiar={setMontoFinal} />
          </label>
        ) : (
          <>
            <label className="campo-operacion">
              <span>Precio por unidad</span>
              <InputNumero valor={precio} prefijo="$" miles alCambiar={setPrecio} />
            </label>
            {sugerido !== null && (
              <button
                type="button"
                className="precio-sugerido"
                title="Cierre de esa rueda: tocá para usarlo"
                onClick={() => setPrecio(sugerido)}
              >
                Cierre de la rueda: ${pesos(sugerido)} — usar
              </button>
            )}
          </>
        )}

        <label className="campo-operacion">
          <span>Nota</span>
          <input
            value={nota}
            placeholder="Opcional"
            onChange={(evento) => setNota(evento.target.value)}
          />
        </label>

        {tasa && (
          <span className={`tasa-aplicada${tasa.es_intradia ? ' intradia' : ''}`}>
            Arancel {tasa.arancel_aplicado_pct}% + mercado {tasa.derechos_mercado_pct}% + IVA{' '}
            {tasa.iva_pct}% = {tasa.tasa_efectiva_pct.toFixed(4)}%
            {tasa.es_intradia && ' — compra-venta en el día'}
          </span>
        )}

        {previsualizacion && (
          <div className="resumen-operacion">
            <div>
              <span>Precio de mercado</span>
              <strong>${pesos(previsualizacion.precio)}</strong>
            </div>
            <div>
              <span>Importe bruto</span>
              <strong>${pesos(previsualizacion.bruto)}</strong>
            </div>
            <div className="gasto">
              <span>Arancel</span>
              <strong>${pesos(previsualizacion.arancel)}</strong>
            </div>
            <div className="gasto">
              <span>Derechos de mercado</span>
              <strong>${pesos(previsualizacion.derechos)}</strong>
            </div>
            <div className="gasto">
              <span>IVA</span>
              <strong>${pesos(previsualizacion.iva)}</strong>
            </div>
            <div className="destacado">
              <span>{tipo === 'compra' ? 'Importe neto a pagar' : 'Importe neto a cobrar'}</span>
              <strong>${pesos(previsualizacion.montoFinal)}</strong>
            </div>
          </div>
        )}

        {mensaje && <div className="mensaje-operacion">{mensaje}</div>}

        <div className="acciones-formulario-operacion">
          <button
            type="button"
            className="boton-guardar-operacion"
            disabled={guardando}
            onClick={() => void guardar()}
          >
            {guardando ? 'Guardando…' : operacion ? 'Guardar cambios' : 'Registrar operación'}
          </button>
          <button type="button" className="boton-cancelar" onClick={alCerrar}>
            Cancelar
          </button>
        </div>
      </div>
    </div>
  )
}

export default FormularioOperacion
