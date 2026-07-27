import { useEffect, useState } from 'react'
import { guardarComisiones, obtenerComisiones } from '../../api/cliente'
import type { Comisiones } from '../../api/tipos'
import InputNumero from '../bots/InputNumero'
import './ConfigComisiones.css'

const CAMPOS: { campo: keyof Comisiones; etiqueta: string; ayuda: string }[] = [
  {
    campo: 'arancel_pct',
    etiqueta: 'Arancel',
    ayuda: 'Comisión del broker sobre el importe bruto',
  },
  {
    campo: 'arancel_intradia_pct',
    etiqueta: 'Arancel intradía',
    ayuda: 'Arancel reducido cuando se compra y vende el mismo papel el mismo día',
  },
  {
    campo: 'derechos_mercado_pct',
    etiqueta: 'Derechos de mercado',
    ayuda: 'Lo que cobra el mercado (BYMA) sobre el importe bruto',
  },
  {
    campo: 'iva_pct',
    etiqueta: 'IVA',
    ayuda: 'Se aplica sobre la suma del arancel y los derechos de mercado',
  },
]

/** Tasas del boleto del broker: se guardan y se usan en cada operación nueva. */
function ConfigComisiones({ alCerrar }: { alCerrar: () => void }) {
  const [config, setConfig] = useState<Comisiones | null>(null)
  const [guardando, setGuardando] = useState(false)
  const [mensaje, setMensaje] = useState('')

  useEffect(() => {
    obtenerComisiones()
      .then(setConfig)
      .catch(() => setMensaje('No se pudieron cargar las tasas'))
  }, [])

  const guardar = async () => {
    if (!config) return
    setGuardando(true)
    setMensaje('')
    try {
      await guardarComisiones(config)
      alCerrar()
    } catch {
      setMensaje('No se pudieron guardar las tasas')
      setGuardando(false)
    }
  }

  const efectiva = config
    ? (config.arancel_pct + config.derechos_mercado_pct) * (1 + config.iva_pct / 100)
    : 0

  return (
    <div className="fondo-config-comisiones" onClick={alCerrar}>
      <div className="config-comisiones" onClick={(evento) => evento.stopPropagation()}>
        <div className="cabecera-config-comisiones">
          <span>Gastos de las operaciones</span>
          <button type="button" className="cerrar-formulario" onClick={alCerrar}>
            ×
          </button>
        </div>

        <p className="ayuda-config">
          Las tasas del boleto de tu broker. Se aplican a cada operación nueva: si cambian
          las condiciones o cambia el IVA, ajustalas acá.
        </p>

        {config && (
          <>
            {CAMPOS.map(({ campo, etiqueta, ayuda }) => (
              <label key={campo} className="campo-comision" title={ayuda}>
                <span>{etiqueta}</span>
                <InputNumero
                  valor={config[campo]}
                  sufijo="%"
                  alCambiar={(valor) => setConfig({ ...config, [campo]: valor ?? 0 })}
                />
              </label>
            ))}

            <div className="efectiva-config">
              <span>Costo total de una operación normal</span>
              <strong>{efectiva.toFixed(4)}%</strong>
            </div>
          </>
        )}

        {mensaje && <span className="mensaje-config">{mensaje}</span>}

        <div className="acciones-config-comisiones">
          <button
            type="button"
            className="boton-guardar-operacion"
            disabled={guardando || !config}
            onClick={() => void guardar()}
          >
            {guardando ? 'Guardando…' : 'Guardar'}
          </button>
          <button type="button" className="boton-cancelar" onClick={alCerrar}>
            Cancelar
          </button>
        </div>
      </div>
    </div>
  )
}

export default ConfigComisiones
