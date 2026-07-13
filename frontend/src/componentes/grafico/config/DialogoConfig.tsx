import { useState } from 'react'
import { usarEstilos, type TipoLinea } from '../../../contextos/EstilosContext'
import type { Temporalidad } from '../../../api/tipos'
import SelectorColor, { nombreColor } from './SelectorColor'
import SelectorLinea from './SelectorLinea'
import EmasExtra from './EmasExtra'
import type { AperturaConfig, ElementoEstilo, GrupoConfig } from './estilosIndicadores'
import { claveGuardada, recomendadoDe } from './paramsIndicadores'
import './config.css'

interface Props {
  apertura: AperturaConfig
  temporalidad: Temporalidad
  alCerrar: () => void
}

/** Diálogo de estilo y parámetros con pestañas (una por grupo: EMA/σ/BB, o una
 *  sola para un oscilador). Aplica en vivo y guarda como default del usuario; el
 *  recomendado se muestra en gris con "Volver". */
function DialogoConfig({ apertura, temporalidad, alCerrar }: Props) {
  const { grupos, titulo } = apertura
  const { estiloDe, overrideDe, guardar, volver, paramsDe, guardarParam, borrarParam } =
    usarEstilos()
  const [activa, setActiva] = useState(0)
  const grupo = grupos[activa] ?? grupos[0]
  // Overrides de parámetros que aplican a la temporalidad actual (los emaCentral
  // se guardan por temporalidad, así que solo cuentan los de esta)
  const overridesGrupo = grupo.indicador ? paramsDe(grupo.indicador) : {}
  const hayParamOverride = (grupo.params ?? []).some(
    (campo) => overridesGrupo[claveGuardada(campo, temporalidad)] !== undefined,
  )
  const hayOverride =
    grupo.elementos.some((e) => Object.keys(overrideDe(e.id)).length > 0) || hayParamOverride

  const seccion = (elem: ElementoEstilo) => {
    const ef = estiloDe(elem.id, elem.recomendado)
    return (
      <div className="seccion-config" key={elem.id}>
        {grupo.elementos.length > 1 && <div className="etiqueta-seccion">{elem.etiqueta}</div>}
        {elem.campos.includes('color') && (
          <div className="campo-config">
            <span className="etiqueta-config">Color</span>
            <SelectorColor
              valor={ef.color ?? '#ffffff'}
              alCambiar={(color) => guardar(elem.id, { color })}
            />
          </div>
        )}
        {elem.campos.includes('linea') && (
          <div className="campo-config">
            <span className="etiqueta-config">Línea</span>
            <SelectorLinea
              ancho={ef.ancho ?? 1}
              tipoLinea={(ef.tipoLinea ?? 'solid') as TipoLinea}
              alCambiarAncho={(ancho) => guardar(elem.id, { ancho })}
              alCambiarTipo={(tipoLinea) => guardar(elem.id, { tipoLinea })}
            />
          </div>
        )}
        {elem.campos.includes('opacidad') && (
          <div className="campo-config">
            <span className="etiqueta-config">Opacidad</span>
            <div className="fila-opacidad">
              <input
                type="range"
                min={10}
                max={100}
                step={5}
                value={Math.round((ef.opacidad ?? 1) * 100)}
                onChange={(e) => guardar(elem.id, { opacidad: Number(e.target.value) / 100 })}
              />
              <span className="valor-opacidad">{Math.round((ef.opacidad ?? 1) * 100)}%</span>
            </div>
          </div>
        )}
        <div className="recomendado-config">
          Recomendado:{' '}
          <b style={{ color: elem.recomendado.color }}>{nombreColor(elem.recomendado.color ?? '')}</b>
          {elem.recomendado.ancho ? ` · ${elem.recomendado.ancho}px` : ''}
        </div>
      </div>
    )
  }

  // Parámetros numéricos del indicador del grupo (período, desvíos…). El campo
  // vacío = usar el recomendado (que se muestra en gris como placeholder).
  const seccionParams = (g: GrupoConfig) => {
    if (!g.indicador || !g.params || g.params.length === 0) {
      return <div className="sin-params">Sin parámetros configurables.</div>
    }
    const indicador = g.indicador
    const overrides = paramsDe(indicador)
    return g.params.map((campo) => {
      const rec = recomendadoDe(campo, temporalidad)
      const clave = claveGuardada(campo, temporalidad)
      const valor = overrides[clave]
      return (
        <div className="campo-config campo-param" key={campo.clave}>
          <span className="etiqueta-config">{campo.etiqueta}</span>
          {campo.opciones ? (
            <select
              className="input-param"
              value={(valor as string) ?? ''}
              onChange={(e) => {
                const bruto = e.target.value
                if (bruto === '') borrarParam(indicador, clave)
                else guardarParam(indicador, clave, bruto)
              }}
            >
              <option value="">
                {campo.opciones.find((o) => o.valor === rec)?.etiqueta ?? rec} (recomendado)
              </option>
              {campo.opciones.map((o) => (
                <option key={o.valor} value={o.valor}>
                  {o.etiqueta}
                </option>
              ))}
            </select>
          ) : (
            <input
              type="number"
              className="input-param"
              min={campo.min}
              step={campo.paso ?? 1}
              value={
                // Un valor guardado por debajo del mínimo (p.ej. 0) se muestra vacío
                typeof valor === 'number' && (campo.min == null || valor >= campo.min)
                  ? valor
                  : ''
              }
              placeholder={`${rec} (recomendado)`}
              onChange={(e) => {
                const bruto = e.target.value
                const n = Number(bruto)
                // Vacío o por debajo del mínimo → sin fijar (usa el recomendado)
                if (bruto === '' || (campo.min != null && n < campo.min)) {
                  borrarParam(indicador, clave)
                } else {
                  guardarParam(indicador, clave, n)
                }
              }}
            />
          )}
        </div>
      )
    })
  }

  return (
    <div className="fondo-config" onClick={alCerrar}>
      <div className="dialogo-config" onClick={(e) => e.stopPropagation()}>
        <div className="cabecera-config">
          <span>{titulo}</span>
          <button type="button" className="cerrar-config" onClick={alCerrar}>×</button>
        </div>

        {grupos.length > 1 && (
          <div className="pestanas-config">
            {grupos.map((g, i) => (
              <button
                key={g.titulo}
                type="button"
                className={i === activa ? 'pestana-config activa' : 'pestana-config'}
                onClick={() => setActiva(i)}
              >
                {g.titulo}
              </button>
            ))}
          </div>
        )}

        <div className="cuerpo-config">
          <div className="columnas-config">
            <div className="columna-config">
              <div className="titulo-columna">Diseño</div>
              {grupo.elementos.map(seccion)}
            </div>
            <div className="columna-config columna-datos">
              <div className="titulo-columna">Datos</div>
              {seccionParams(grupo)}
            </div>
          </div>
          {grupo.emasExtra && <EmasExtra temporalidad={temporalidad} />}
        </div>

        <div className="pie-config">
          <button
            type="button"
            className="volver-config"
            disabled={!hayOverride}
            onClick={() => {
              grupo.elementos.forEach((e) => volver(e.id))
              if (grupo.indicador) {
                ;(grupo.params ?? []).forEach((campo) =>
                  borrarParam(grupo.indicador!, claveGuardada(campo, temporalidad)),
                )
              }
            }}
          >
            Volver a lo recomendado
          </button>
        </div>
      </div>
    </div>
  )
}

export default DialogoConfig
