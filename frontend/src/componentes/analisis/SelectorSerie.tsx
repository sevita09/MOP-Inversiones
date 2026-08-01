import { usarTickers } from '../../hooks/usarTickers'

export const INFLACION = 'INFLACION'

interface Props {
  valor: string
  alCambiar: (serie: string) => void
  /** La inflación solo existe mensual: en D y S no se ofrece */
  temporalidad?: string
  etiqueta?: string
}

/** Un desplegable con todo el universo, agrupado para que se pueda encontrar
 *  algo entre ciento ochenta opciones. */
function SelectorSerie({ valor, alCambiar, temporalidad = 'D', etiqueta }: Props) {
  const paneles = usarTickers()
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

  return (
    <select
      value={valor}
      onChange={(evento) => alCambiar(evento.target.value)}
      aria-label={etiqueta}
    >
      <option value="">elegir</option>
      {grupos.map(({ nombre, tickers }) => (
        <optgroup key={nombre} label={nombre}>
          {[...tickers].sort().map((papel) => (
            <option key={papel} value={papel}>
              {papel}
            </option>
          ))}
        </optgroup>
      ))}
    </select>
  )
}

export default SelectorSerie
