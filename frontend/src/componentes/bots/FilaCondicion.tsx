import type { CondicionRegla, ObjetivoSerie, OperadorRegla } from '../../api/tipos'
import {
  ES_OPERADOR_PRECIO,
  INDICADORES_REGLAS,
  OPERADORES_REGLAS,
} from './configReglas'

interface Props {
  condicion: CondicionRegla
  alCambiar: (condicion: CondicionRegla) => void
  alQuitar: () => void
}

function esObjetivoSerie(objetivo: CondicionRegla['objetivo']): objetivo is ObjetivoSerie {
  return typeof objetivo === 'object' && objetivo !== null
}

/** Una condición editable: indicador · serie · operador · objetivo. */
function FilaCondicion({ condicion, alCambiar, alQuitar }: Props) {
  const info = INDICADORES_REGLAS[condicion.indicador]
  const objetivoSerie = esObjetivoSerie(condicion.objetivo) ? condicion.objetivo : null
  const esPrecio = ES_OPERADOR_PRECIO(condicion.operador)

  const cambiarIndicador = (indicador: string) => {
    // Serie y objetivo vuelven al default del indicador nuevo: no tienen sentido cruzado
    const primera = INDICADORES_REGLAS[indicador].series[0].valor
    alCambiar({ ...condicion, indicador, serie: primera, objetivo: esPrecio ? undefined : 0 })
  }

  const cambiarOperador = (operador: OperadorRegla) => {
    if (ES_OPERADOR_PRECIO(operador)) {
      alCambiar({ ...condicion, operador, objetivo: undefined })
    } else {
      const objetivo = condicion.objetivo ?? 0
      alCambiar({ ...condicion, operador, objetivo })
    }
  }

  const cambiarTipoObjetivo = (tipo: string) => {
    if (tipo === 'serie') {
      const otra = info.series.find((s) => s.valor !== condicion.serie) ?? info.series[0]
      alCambiar({ ...condicion, objetivo: { serie: otra.valor } })
    } else {
      alCambiar({ ...condicion, objetivo: 0 })
    }
  }

  return (
    <div className="fila-condicion">
      <select
        value={condicion.indicador}
        onChange={(evento) => cambiarIndicador(evento.target.value)}
      >
        {Object.entries(INDICADORES_REGLAS).map(([valor, { etiqueta }]) => (
          <option key={valor} value={valor}>
            {etiqueta}
          </option>
        ))}
      </select>

      {info.series.length > 1 && (
        <select
          value={condicion.serie}
          onChange={(evento) => alCambiar({ ...condicion, serie: evento.target.value })}
        >
          {info.series.map(({ valor, etiqueta }) => (
            <option key={valor} value={valor}>
              {etiqueta}
            </option>
          ))}
        </select>
      )}

      <select
        value={condicion.operador}
        onChange={(evento) => cambiarOperador(evento.target.value as OperadorRegla)}
      >
        {OPERADORES_REGLAS.map(({ valor, etiqueta }) => (
          <option key={valor} value={valor}>
            {etiqueta}
          </option>
        ))}
      </select>

      {!esPrecio && (
        <>
          <select
            value={objetivoSerie ? 'serie' : 'constante'}
            onChange={(evento) => cambiarTipoObjetivo(evento.target.value)}
          >
            <option value="constante">un valor</option>
            {info.series.length > 1 && <option value="serie">otra serie</option>}
          </select>
          {objetivoSerie ? (
            <select
              value={objetivoSerie.serie}
              onChange={(evento) =>
                alCambiar({ ...condicion, objetivo: { serie: evento.target.value } })
              }
            >
              {info.series
                .filter(({ valor }) => valor !== condicion.serie)
                .map(({ valor, etiqueta }) => (
                  <option key={valor} value={valor}>
                    {etiqueta}
                  </option>
                ))}
            </select>
          ) : (
            <input
              type="number"
              step="any"
              className="objetivo-condicion"
              value={typeof condicion.objetivo === 'number' ? condicion.objetivo : 0}
              onChange={(evento) =>
                alCambiar({ ...condicion, objetivo: Number(evento.target.value) })
              }
            />
          )}
        </>
      )}

      <button type="button" className="quitar-condicion" title="Quitar condición" onClick={alQuitar}>
        ×
      </button>
    </div>
  )
}

export default FilaCondicion
