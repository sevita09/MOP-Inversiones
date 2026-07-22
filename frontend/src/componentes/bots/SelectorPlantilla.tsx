import { useState } from 'react'
import type { Plantilla } from '../../api/tipos'

interface Props {
  plantillas: Plantilla[]
  alElegir: (plantilla: Plantilla) => void
  alLimpiar: () => void
  alEliminar: (id: number) => void
}

/** Elegir una estrategia precarga nombre, moneda, temporalidad y reglas (después
 *  se puede editar todo). Separa las de la metodología de las plantillas propias;
 *  las propias se pueden borrar. */
function SelectorPlantilla({ plantillas, alElegir, alLimpiar, alEliminar }: Props) {
  const [clave, setClave] = useState('')

  if (plantillas.length === 0) return null
  const elegida = plantillas.find((plantilla) => plantilla.clave === clave)
  const predefinidas = plantillas.filter((p) => p.predefinida)
  const propias = plantillas.filter((p) => !p.predefinida)

  return (
    <div className="campo-bot">
      Plantilla de estrategia
      <select
        value={clave}
        onChange={(evento) => {
          setClave(evento.target.value)
          const plantilla = plantillas.find((p) => p.clave === evento.target.value)
          // "Desde cero" limpia las reglas que había cargado la plantilla anterior
          if (plantilla) alElegir(plantilla)
          else alLimpiar()
        }}
      >
        <option value="">Desde cero</option>
        <optgroup label="Plantillas base">
          {predefinidas.map(({ clave: valor, nombre }) => (
            <option key={valor} value={valor}>
              {nombre}
            </option>
          ))}
        </optgroup>
        {propias.length > 0 && (
          <optgroup label="Propias">
            {propias.map(({ clave: valor, nombre }) => (
              <option key={valor} value={valor}>
                {nombre}
              </option>
            ))}
          </optgroup>
        )}
      </select>
      {elegida && (
        <span className="descripcion-plantilla">
          {elegida.descripcion}
          <span className="horizonte-plantilla">{elegida.horizonte}</span>
          {!elegida.predefinida && elegida.id !== null && (
            <button
              type="button"
              className="borrar-plantilla"
              onClick={() => {
                alEliminar(elegida.id as number)
                setClave('')
              }}
            >
              Borrar esta plantilla
            </button>
          )}
        </span>
      )}
    </div>
  )
}

export default SelectorPlantilla
