import { useState } from 'react'
import type { RiesgoBot } from '../../api/tipos'
import { usarPresetsRiesgo } from '../../hooks/usarPresetsRiesgo'
import InputNumero from './InputNumero'
import './ControlesRiesgo.css'

interface Props {
  riesgo: RiesgoBot
  alCambiar: (riesgo: RiesgoBot) => void
}

export const RIESGO_VACIO: RiesgoBot = {
  stop_loss_pct: null,
  stop_atr_mult: null,
  take_profit_pct: null,
  salida_ema_central: false,
  trailing_pct: null,
  atr_periodo: 14,
  sizing_riesgo_pct: null,
}

/** True si la config de riesgo tiene algo cargado (para abrir el panel solo). */
export function tieneRiesgo(r: RiesgoBot): boolean {
  return (
    r.stop_loss_pct !== null ||
    r.stop_atr_mult !== null ||
    r.take_profit_pct !== null ||
    r.trailing_pct !== null ||
    r.sizing_riesgo_pct !== null ||
    r.salida_ema_central
  )
}

const AYUDA_STOP_LOSS = 'Vende automáticamente si el precio cae ese % por debajo del precio de entrada. Corta la pérdida.'
const AYUDA_TAKE_PROFIT = 'Vende automáticamente cuando la ganancia llega a ese % sobre el precio de entrada. Asegura la ganancia.'
const AYUDA_TRAILING = 'Un stop que acompaña la subida: se ubica ese % por debajo del máximo alcanzado y nunca baja. Deja correr la ganancia pero la protege si el precio se da vuelta.'
const AYUDA_ATR_STOP = 'Igual que el stop loss, pero la distancia se mide en ATR (volatilidad del papel): stop a N veces el ATR bajo la entrada. Se adapta a cada activo.'
const AYUDA_ATR_PERIODO = 'Cantidad de barras para calcular el ATR que usan el stop por ATR y el sizing por riesgo. Típico: 14.'
const AYUDA_SIZING = 'En vez de invertir un monto fijo, calcula cuántas acciones comprar para que, si salta el stop, la pérdida sea exactamente ese % del capital. Necesita un stop definido.'
const AYUDA_EMA = 'Vende cuando el precio de cierre cruza hacia abajo la EMA central de la temporalidad (la media de la metodología). Una salida por pérdida de tendencia.'

/** Ícono ⓘ con la explicación al pasar el mouse (solo en conceptos técnicos). */
function Info({ texto }: { texto: string }) {
  return (
    <span className="info-riesgo" title={texto} aria-label={texto}>
      ⓘ
    </span>
  )
}

/** Controles de gestión de riesgo del bot (se aplican en el backtest). */
function ControlesRiesgo({ riesgo, alCambiar }: Props) {
  const { presets, crear, eliminar } = usarPresetsRiesgo()
  const [abierto, setAbierto] = useState(() => tieneRiesgo(riesgo))
  const [guardando, setGuardando] = useState(false)
  const [nombrePreset, setNombrePreset] = useState('')
  const [mensaje, setMensaje] = useState('')
  const [presetElegido, setPresetElegido] = useState('')

  const set = (campo: keyof RiesgoBot, valor: number | null) =>
    alCambiar({ ...riesgo, [campo]: valor })

  const hayStop = riesgo.stop_loss_pct !== null || riesgo.stop_atr_mult !== null
  const usaAtr = riesgo.stop_atr_mult !== null || riesgo.sizing_riesgo_pct !== null

  const guardarPreset = async () => {
    const limpio = nombrePreset.trim()
    if (!limpio) return setMensaje('Poné un nombre al preset')
    setGuardando(true)
    setMensaje('')
    try {
      await crear(limpio, riesgo)
      setNombrePreset('')
    } catch (error) {
      const texto = error instanceof Error ? error.message : ''
      setMensaje(texto.includes('409') ? `Ya existe un preset llamado ${limpio}` : 'No se pudo guardar')
    } finally {
      setGuardando(false)
    }
  }

  return (
    <details className="controles-riesgo" open={abierto} onToggle={(e) => setAbierto(e.currentTarget.open)}>
      <summary>Gestión de riesgo (opcional)</summary>

      <div className="presets-riesgo">
        <select
          value={presetElegido}
          onChange={(evento) => {
            const id = evento.target.value
            setPresetElegido(id)
            const preset = presets.find((p) => String(p.id) === id)
            if (preset) alCambiar({ ...preset.riesgo })
          }}
        >
          <option value="">Aplicar preset…</option>
          {presets.map((preset) => (
            <option key={preset.id} value={preset.id}>
              {preset.nombre}
            </option>
          ))}
        </select>
        {presetElegido && (
          <button
            type="button"
            className="borrar-preset"
            title="Borrar este preset"
            onClick={() => {
              void eliminar(Number(presetElegido))
              setPresetElegido('')
            }}
          >
            🗑
          </button>
        )}
      </div>

      <div className="grilla-riesgo">
        <label className="campo-riesgo">
          <span>
            Stop loss <Info texto={AYUDA_STOP_LOSS} />
          </span>
          <InputNumero valor={riesgo.stop_loss_pct} sufijo="%" alCambiar={(v) => set('stop_loss_pct', v)} />
        </label>
        <label className="campo-riesgo">
          <span>
            Take profit <Info texto={AYUDA_TAKE_PROFIT} />
          </span>
          <InputNumero valor={riesgo.take_profit_pct} sufijo="%" alCambiar={(v) => set('take_profit_pct', v)} />
        </label>

        <label className="campo-riesgo">
          <span>
            Trailing stop <Info texto={AYUDA_TRAILING} />
          </span>
          <InputNumero valor={riesgo.trailing_pct} sufijo="%" alCambiar={(v) => set('trailing_pct', v)} />
        </label>
        <label className="campo-riesgo">
          <span>
            Riesgo por trade <Info texto={AYUDA_SIZING} />
          </span>
          <InputNumero
            valor={riesgo.sizing_riesgo_pct}
            sufijo="%"
            disabled={!hayStop}
            alCambiar={(v) => set('sizing_riesgo_pct', v)}
          />
        </label>

        <label className="campo-riesgo">
          <span>
            Stop por ATR <Info texto={AYUDA_ATR_STOP} />
          </span>
          <InputNumero valor={riesgo.stop_atr_mult} sufijo="× ATR" alCambiar={(v) => set('stop_atr_mult', v)} />
        </label>
        <label className="campo-riesgo">
          <span>
            Período ATR <Info texto={AYUDA_ATR_PERIODO} />
          </span>
          <InputNumero
            valor={riesgo.atr_periodo}
            disabled={!usaAtr}
            alCambiar={(v) => set('atr_periodo', v ?? 14)}
          />
        </label>
      </div>

      <label className="check-riesgo">
        <input
          type="checkbox"
          checked={riesgo.salida_ema_central}
          onChange={(evento) => alCambiar({ ...riesgo, salida_ema_central: evento.target.checked })}
        />
        Salir al cruzar la EMA central hacia abajo
        <Info texto={AYUDA_EMA} />
      </label>

      {tieneRiesgo(riesgo) && (
        <div className="guardar-preset-riesgo">
          <input
            value={nombrePreset}
            placeholder="Guardar esta gestión como…"
            onChange={(evento) => setNombrePreset(evento.target.value)}
          />
          <button
            type="button"
            className="boton-guardar-preset"
            disabled={guardando}
            onClick={() => void guardarPreset()}
          >
            {guardando ? '…' : 'Guardar preset'}
          </button>
        </div>
      )}
      {mensaje && <span className="mensaje-preset">{mensaje}</span>}
    </details>
  )
}

export default ControlesRiesgo
