import type { Temporalidad } from '../../../api/tipos'
import type { TipoLinea } from '../../../contextos/EstilosContext'
import {
  usarEmasExtra,
  tipoExtraDe,
  PERIODO_EXTRA_DEFAULT,
  ANCHO_EXTRA_DEFAULT,
  TIPO_LINEA_EXTRA_DEFAULT,
  type TipoMedia,
} from '../../../contextos/EmasExtraContext'
import { OPCIONES_TIPO_MEDIA } from './paramsIndicadores'
import SelectorColor from './SelectorColor'

const ANCHOS = [1, 2, 3, 4]
const TIPOS_LINEA: { valor: TipoLinea; etiqueta: string }[] = [
  { valor: 'solid', etiqueta: 'Sólida' },
  { valor: 'dashed', etiqueta: 'Guiones' },
  { valor: 'dotted', etiqueta: 'Puntos' },
]

interface Props {
  temporalidad: Temporalidad
}

/** Sección de la pestaña EMA central: agregar/quitar EMAs extra sobre el precio.
 *  El período y el tipo se guardan por temporalidad; el color es único. */
function EmasExtra({ temporalidad }: Props) {
  const { emas, agregar, quitar, setColor, setLinea, setPeriodo, setTipo } = usarEmasExtra()

  return (
    <div className="emas-extra">
      <div className="titulo-columna">EMAs extra ({temporalidad})</div>

      {emas.map((ema) => (
        <div className="ema-extra" key={ema.id}>
          <div className="ema-extra-cab">
            <span className="ema-extra-punto" style={{ backgroundColor: ema.color }} />
            <span className="ema-extra-nombre">
              {tipoExtraDe(ema, temporalidad) === 'simple' ? 'SMA' : 'EMA'}{' '}
              {ema.periodo[temporalidad] ?? PERIODO_EXTRA_DEFAULT}
            </span>
            <button
              type="button"
              className="ema-extra-quitar"
              title="Quitar esta EMA"
              onClick={() => quitar(ema.id)}
            >
              ×
            </button>
          </div>

          <div className="ema-extra-campos">
            <div className="campo-config">
              <span className="etiqueta-config">Período</span>
              <input
                type="number"
                className="input-param"
                min={1}
                value={ema.periodo[temporalidad] ?? ''}
                placeholder={`${PERIODO_EXTRA_DEFAULT}`}
                onChange={(e) => {
                  const v = e.target.value
                  const n = Number(v)
                  setPeriodo(ema.id, temporalidad, v === '' || n < 1 ? undefined : n)
                }}
              />
            </div>
            <div className="campo-config">
              <span className="etiqueta-config">Tipo</span>
              <select
                className="input-param"
                value={tipoExtraDe(ema, temporalidad)}
                onChange={(e) => setTipo(ema.id, temporalidad, e.target.value as TipoMedia)}
              >
                {OPCIONES_TIPO_MEDIA.map((o) => (
                  <option key={o.valor} value={o.valor}>
                    {o.etiqueta}
                  </option>
                ))}
              </select>
            </div>
            <div className="campo-config">
              <span className="etiqueta-config">Ancho</span>
              <select
                className="input-param"
                value={ema.ancho ?? ANCHO_EXTRA_DEFAULT}
                onChange={(e) => setLinea(ema.id, { ancho: Number(e.target.value) })}
              >
                {ANCHOS.map((a) => (
                  <option key={a} value={a}>
                    {a}px
                  </option>
                ))}
              </select>
            </div>
            <div className="campo-config">
              <span className="etiqueta-config">Línea</span>
              <select
                className="input-param"
                value={ema.tipoLinea ?? TIPO_LINEA_EXTRA_DEFAULT}
                onChange={(e) => setLinea(ema.id, { tipoLinea: e.target.value as TipoLinea })}
              >
                {TIPOS_LINEA.map((o) => (
                  <option key={o.valor} value={o.valor}>
                    {o.etiqueta}
                  </option>
                ))}
              </select>
            </div>
          </div>

          <div className="campo-config">
            <span className="etiqueta-config">Color</span>
            <SelectorColor valor={ema.color} alCambiar={(c) => setColor(ema.id, c)} />
          </div>
        </div>
      ))}

      <button type="button" className="agregar-ema" onClick={agregar}>
        + Agregar EMA
      </button>
    </div>
  )
}

export default EmasExtra
