import { usarTickers } from '../../hooks/usarTickers'
import './SelectorPapeles.css'

interface Props {
  elegidos: string[]
  alCambiar: (papeles: string[]) => void
  maximo?: number
  /** La inflación solo existe mensual: en D y S no se ofrece */
  temporalidad?: string
}

const INFLACION = 'INFLACION'

/** Las referencias contra las que uno quiere medir un papel argentino.
 *
 *  Van a un clic y no perdidas entre las ciento ochenta opciones del
 *  desplegable: son la mitad de las preguntas que se le hacen a esta pantalla. */
const REFERENCIAS: { ticker: string; etiqueta: string; soloMensual?: boolean }[] = [
  { ticker: 'DOLARMEP', etiqueta: 'Dólar MEP' },
  { ticker: 'DOLARCCL', etiqueta: 'Dólar CCL' },
  { ticker: 'DOLAROF', etiqueta: 'Dólar oficial' },
  { ticker: 'MERVAL', etiqueta: 'MERVAL' },
  { ticker: 'SPY', etiqueta: 'S&P 500' },
  { ticker: 'QQQ', etiqueta: 'Nasdaq' },
  { ticker: 'BTC', etiqueta: 'Bitcoin' },
  { ticker: INFLACION, etiqueta: 'Inflación', soloMensual: true },
]

/** Chips con las series de la matriz, atajos a las referencias y un
 *  desplegable agrupado para sumar cualquier otra. */
function SelectorPapeles({ elegidos, alCambiar, maximo = 12, temporalidad = 'D' }: Props) {
  const paneles = usarTickers()
  const lleno = elegidos.length >= maximo

  const grupos = paneles
    ? [
        { nombre: 'Dólar', tickers: paneles.dolar },
        { nombre: 'Índices', tickers: paneles.indices },
        { nombre: 'Panel líder', tickers: paneles.panel_lider },
        { nombre: 'Panel general', tickers: paneles.panel_general },
        { nombre: 'CEDEARs', tickers: paneles.cedears },
        { nombre: 'Cripto', tickers: paneles.cripto },
        ...(temporalidad === 'M' ? [{ nombre: 'Otras series', tickers: [INFLACION] }] : []),
      ]
    : []

  const referencias = REFERENCIAS.filter(
    (r) => (!r.soloMensual || temporalidad === 'M') && !elegidos.includes(r.ticker),
  )

  return (
    <div className="selector-papeles">
      <div className="fila-papeles">
        {elegidos.map((papel) => (
          <span key={papel} className="chip-papel">
            {papel}
            <button
              type="button"
              title={`Sacar ${papel} de la matriz`}
              onClick={() => alCambiar(elegidos.filter((t) => t !== papel))}
            >
              ×
            </button>
          </span>
        ))}
        {!lleno && (
          <select
            className="agregar-papel"
            value=""
            onChange={(evento) => {
              if (evento.target.value) alCambiar([...elegidos, evento.target.value])
            }}
          >
            <option value="">＋ agregar</option>
            {grupos.map(({ nombre, tickers }) => (
              <optgroup key={nombre} label={nombre}>
                {tickers
                  .filter((t) => !elegidos.includes(t))
                  .sort()
                  .map((papel) => (
                    <option key={papel} value={papel}>
                      {papel}
                    </option>
                  ))}
              </optgroup>
            ))}
          </select>
        )}
        {lleno && <span className="tope-papeles">máximo {maximo} series</span>}
      </div>

      {!lleno && referencias.length > 0 && (
        <div className="fila-referencias">
          <span className="rotulo-referencias">Comparar contra</span>
          {referencias.map(({ ticker, etiqueta }) => (
            <button
              key={ticker}
              type="button"
              className="atajo-referencia"
              onClick={() => alCambiar([...elegidos, ticker])}
            >
              ＋ {etiqueta}
            </button>
          ))}
        </div>
      )}
    </div>
  )
}

export default SelectorPapeles
