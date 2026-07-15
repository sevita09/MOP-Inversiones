import type { CondicionRegla, ReglasBot } from '../../api/tipos'
import FilaCondicion from './FilaCondicion'
import { CONDICION_NUEVA } from './configReglas'
import './ConstructorReglas.css'

interface Props {
  reglas: ReglasBot
  alCambiar: (reglas: ReglasBot) => void
}

type Bloque = 'entrada' | 'salida' | 'filtros'

const BLOQUES: { clave: Bloque; titulo: string; descripcion: string }[] = [
  { clave: 'entrada', titulo: 'Entrada', descripcion: 'compra cuando se cumplen todas' },
  { clave: 'salida', titulo: 'Salida', descripcion: 'vende cuando se cumplen todas' },
  { clave: 'filtros', titulo: 'Filtros', descripcion: 'condiciones extra para la entrada' },
]

/** Editor visual de reglas: tres bloques de condiciones combinadas con AND. */
function ConstructorReglas({ reglas, alCambiar }: Props) {
  const cambiarBloque = (bloque: Bloque, condiciones: CondicionRegla[]) => {
    alCambiar({ ...reglas, [bloque]: condiciones })
  }

  return (
    <div className="constructor-reglas">
      {BLOQUES.map(({ clave, titulo, descripcion }) => {
        const condiciones = reglas[clave]
        // Los filtros solo se muestran si hay (los agrega la plantilla o el usuario avanzado)
        if (clave === 'filtros' && condiciones.length === 0) return null
        return (
          <section key={clave} className="bloque-reglas">
            <header className="cabecera-bloque">
              <span className={`titulo-bloque ${clave}`}>{titulo}</span>
              <span className="descripcion-bloque">{descripcion}</span>
            </header>
            {condiciones.length === 0 && (
              <p className="bloque-vacio">Sin condiciones — este bloque no dispara.</p>
            )}
            {condiciones.map((condicion, indice) => (
              <FilaCondicion
                key={indice}
                condicion={condicion}
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
