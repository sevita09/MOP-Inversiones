import type { CondicionRegla, ReglasBot, TemporalidadBot } from '../../api/tipos'
import FilaCondicion from './FilaCondicion'
import { CONDICION_NUEVA } from './configReglas'
import './ConstructorReglas.css'

interface Props {
  reglas: ReglasBot
  temporalidadBot: TemporalidadBot
  alCambiar: (reglas: ReglasBot) => void
}

type Bloque = 'entrada' | 'salida' | 'filtros'

const BLOQUES: { clave: Bloque; titulo: string; descripcion: string; vacio: string }[] = [
  {
    clave: 'entrada',
    titulo: 'Entrada',
    descripcion: 'compra cuando se cumplen todas',
    vacio: 'Sin condiciones — el bot no compra.',
  },
  {
    clave: 'salida',
    titulo: 'Salida',
    descripcion: 'vende cuando se cumplen todas',
    vacio: 'Sin condiciones — el bot no vende por reglas.',
  },
  {
    clave: 'filtros',
    titulo: 'Filtros',
    descripcion: 'condiciones de contexto que también deben cumplirse para comprar',
    vacio: 'Sin filtros — la entrada no exige contexto extra.',
  },
]

/** Editor visual de reglas: tres bloques de condiciones combinadas con AND. */
function ConstructorReglas({ reglas, temporalidadBot, alCambiar }: Props) {
  const cambiarBloque = (bloque: Bloque, condiciones: CondicionRegla[]) => {
    alCambiar({ ...reglas, [bloque]: condiciones })
  }

  return (
    <div className="constructor-reglas">
      {BLOQUES.map(({ clave, titulo, descripcion, vacio }) => {
        const condiciones = reglas[clave]
        return (
          <section key={clave} className="bloque-reglas">
            <header className="cabecera-bloque">
              <span className={`titulo-bloque ${clave}`}>{titulo}</span>
              <span className="descripcion-bloque">{descripcion}</span>
            </header>
            {condiciones.length === 0 && <p className="bloque-vacio">{vacio}</p>}
            {condiciones.map((condicion, indice) => (
              <FilaCondicion
                key={indice}
                condicion={condicion}
                temporalidadBot={temporalidadBot}
                alCambiar={(nueva) =>
                  cambiarBloque(
                    clave,
                    condiciones.map((c, i) => (i === indice ? nueva : c)),
                  )
                }
                alQuitar={() =>
                  cambiarBloque(
                    clave,
                    condiciones.filter((_, i) => i !== indice),
                  )
                }
              />
            ))}
            <button
              type="button"
              className="agregar-condicion"
              onClick={() => cambiarBloque(clave, [...condiciones, { ...CONDICION_NUEVA }])}
            >
              ＋ condición
            </button>
          </section>
        )
      })}
    </div>
  )
}

export default ConstructorReglas
