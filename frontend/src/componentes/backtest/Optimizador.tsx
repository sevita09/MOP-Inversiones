import { useMemo, useState } from 'react'
import type { Bot, MetricaOptimizacion, ParametroOptimizacion } from '../../api/tipos'
import InputNumero from '../bots/InputNumero'
import { usarOptimizacion } from '../../hooks/usarOptimizacion'
import ResultadosOptimizacion from './ResultadosOptimizacion'
import { opcionesOptimizables } from './opcionesOptimizables'
import './Optimizador.css'

interface Props {
  bot: Bot
}

const METRICAS: { valor: MetricaOptimizacion; etiqueta: string }[] = [
  { valor: 'retorno_pct', etiqueta: 'Retorno' },
  { valor: 'sharpe', etiqueta: 'Sharpe' },
  { valor: 'profit_factor', etiqueta: 'Profit factor' },
  { valor: 'expectancy_pct', etiqueta: 'Resultado medio' },
]

interface Rango {
  desde: number | null
  hasta: number | null
  paso: number | null
}

/** Grid search sobre uno o dos parámetros del bot, con walk-forward. */
function Optimizador({ bot }: Props) {
  const opciones = useMemo(() => opcionesOptimizables(bot), [bot])
  const { estado, mensaje, optimizar } = usarOptimizacion()
  const [metrica, setMetrica] = useState<MetricaOptimizacion>('retorno_pct')
  const [claves, setClaves] = useState<[string, string]>(['', ''])
  const [rangos, setRangos] = useState<[Rango, Rango]>([
    { desde: null, hasta: null, paso: null },
    { desde: null, hasta: null, paso: null },
  ])

  if (opciones.length === 0) {
    return (
      <p className="optimizador-vacio">
        Este bot no tiene umbrales ni parámetros de riesgo numéricos para optimizar.
      </p>
    )
  }

  const elegir = (posicion: 0 | 1, clave: string) => {
    const siguientes: [string, string] = [...claves]
    siguientes[posicion] = clave
    setClaves(siguientes)
    // Al elegir, precargar el rango sugerido alrededor del valor actual
    const opcion = opciones.find((o) => o.clave === clave)
    const nuevos: [Rango, Rango] = [...rangos]
    nuevos[posicion] = opcion
      ? { desde: opcion.desde, hasta: opcion.hasta, paso: opcion.paso }
      : { desde: null, hasta: null, paso: null }
    setRangos(nuevos)
  }

  const cambiarRango = (posicion: 0 | 1, campo: keyof Rango, valor: number | null) => {
    const nuevos: [Rango, Rango] = [...rangos]
    nuevos[posicion] = { ...nuevos[posicion], [campo]: valor }
    setRangos(nuevos)
  }

  const armarParametros = (): ParametroOptimizacion[] => {
    const parametros: ParametroOptimizacion[] = []
    for (const posicion of [0, 1] as const) {
      const opcion = opciones.find((o) => o.clave === claves[posicion])
      const rango = rangos[posicion]
      if (!opcion || rango.desde === null || rango.hasta === null || !rango.paso) continue
      parametros.push({ ...opcion.base, desde: rango.desde, hasta: rango.hasta, paso: rango.paso })
    }
    return parametros
  }

  const parametros = armarParametros()
  const combinaciones = parametros.reduce((total, p) => {
    const cantidad = Math.floor((p.hasta - p.desde) / p.paso) + 1
    return total * Math.max(cantidad, 0)
  }, 1)

  const disponibles = (posicion: 0 | 1) =>
    opciones.filter((o) => o.clave === claves[posicion] || o.clave !== claves[posicion === 0 ? 1 : 0])

  return (
    <div className="optimizador">
      <p className="ayuda-optimizador">
        Barre uno o dos parámetros y evalúa cada combinación. Optimiza sobre el 70% más viejo de la
        historia y valida la mejor en el 30% final, que nunca vio: así se detecta el sobreajuste.
      </p>

      <div className="controles-optimizador">
        {([0, 1] as const).map((posicion) => (
          <div key={posicion} className="parametro-optimizador">
            <label className="campo-optimizador">
              <span>{posicion === 0 ? 'Parámetro' : 'Segundo parámetro (opcional)'}</span>
              <select value={claves[posicion]} onChange={(e) => elegir(posicion, e.target.value)}>
                <option value="">{posicion === 0 ? 'Elegí uno…' : 'Ninguno'}</option>
                {disponibles(posicion).map((opcion) => (
                  <option key={opcion.clave} value={opcion.clave}>
                    {opcion.etiqueta} (hoy {opcion.actual})
                  </option>
                ))}
              </select>
            </label>
            {claves[posicion] && (
              <div className="rango-optimizador">
                <label>
                  <span>Desde</span>
                  <InputNumero
                    valor={rangos[posicion].desde}
                    alCambiar={(v) => cambiarRango(posicion, 'desde', v)}
                  />
                </label>
                <label>
                  <span>Hasta</span>
                  <InputNumero
                    valor={rangos[posicion].hasta}
                    alCambiar={(v) => cambiarRango(posicion, 'hasta', v)}
                  />
                </label>
                <label>
                  <span>Paso</span>
                  <InputNumero
                    valor={rangos[posicion].paso}
                    alCambiar={(v) => cambiarRango(posicion, 'paso', v)}
                  />
                </label>
              </div>
            )}
          </div>
        ))}

        <label className="campo-optimizador metrica-optimizador">
          <span>Optimizar por</span>
          <select value={metrica} onChange={(e) => setMetrica(e.target.value as MetricaOptimizacion)}>
            {METRICAS.map(({ valor, etiqueta }) => (
              <option key={valor} value={valor}>
                {etiqueta}
              </option>
            ))}
          </select>
        </label>
      </div>

      <div className="acciones-optimizador">
        <button
          type="button"
          className="boton-optimizar"
          disabled={parametros.length === 0 || estado.en_curso}
          onClick={() => void optimizar(bot.id, parametros, metrica)}
        >
          {estado.en_curso ? 'Optimizando…' : 'Optimizar'}
        </button>
        {parametros.length > 0 && !estado.en_curso && (
          <span className="conteo-combinaciones">{combinaciones} combinaciones a probar</span>
        )}
        {estado.en_curso && estado.total > 0 && (
          <span className="progreso-optimizador">
            <progress value={estado.hechos} max={estado.total} />
            {estado.hechos} / {estado.total}
          </span>
        )}
        {mensaje && <span className="error-optimizador">{mensaje}</span>}
        {estado.error && <span className="error-optimizador">{estado.error}</span>}
      </div>

      {estado.resultado && !estado.en_curso && (
        <ResultadosOptimizacion resultado={estado.resultado} opciones={opciones} />
      )}
    </div>
  )
}

export default Optimizador
