import { useState } from 'react'
import type { Moneda, PlantillaNueva, ReglasBot, TemporalidadBot } from '../../api/tipos'
import { reglasConContenido } from './configReglas'

interface Props {
  reglas: ReglasBot
  temporalidad: TemporalidadBot
  moneda: Moneda
  nombreSugerido: string
  alCrear: (datos: PlantillaNueva) => Promise<unknown>
}

/** Guarda las reglas actuales como una plantilla propia reutilizable. */
function GuardarComoPlantilla({ reglas, temporalidad, moneda, nombreSugerido, alCrear }: Props) {
  const [abierto, setAbierto] = useState(false)
  const [nombre, setNombre] = useState('')
  const [descripcion, setDescripcion] = useState('')
  const [mensaje, setMensaje] = useState('')
  const [guardando, setGuardando] = useState(false)

  // Sin al menos una condición de entrada no hay estrategia que guardar
  if (!reglasConContenido(reglas)) return null

  const abrir = () => {
    setNombre(nombreSugerido)
    setDescripcion('')
    setMensaje('')
    setAbierto(true)
  }

  const guardar = async () => {
    const limpio = nombre.trim()
    if (!limpio) return setMensaje('Poné un nombre a la plantilla')
    setGuardando(true)
    setMensaje('')
    try {
      await alCrear({ nombre: limpio, descripcion: descripcion.trim(), temporalidad, moneda, reglas })
      setAbierto(false)
    } catch (error) {
      const texto = error instanceof Error ? error.message : ''
      setMensaje(
        texto.includes('409')
          ? `Ya existe una plantilla llamada ${limpio}`
          : 'No se pudo guardar la plantilla',
      )
    } finally {
      setGuardando(false)
    }
  }

  if (!abierto) {
    return (
      <button type="button" className="guardar-como-plantilla" onClick={abrir}>
        ＋ Guardar como plantilla
      </button>
    )
  }

  return (
    <div className="panel-guardar-plantilla">
      <input
        autoFocus
        value={nombre}
        placeholder="Nombre de la plantilla"
        onChange={(evento) => setNombre(evento.target.value)}
      />
      <input
        value={descripcion}
        placeholder="Descripción (opcional)"
        onChange={(evento) => setDescripcion(evento.target.value)}
      />
      {mensaje && <span className="mensaje-plantilla">{mensaje}</span>}
      <div className="acciones-guardar-plantilla">
        <button
          type="button"
          className="boton-guardar-bot"
          disabled={guardando}
          onClick={() => void guardar()}
        >
          {guardando ? 'Guardando…' : 'Guardar plantilla'}
        </button>
        <button type="button" className="boton-cancelar" onClick={() => setAbierto(false)}>
          Cancelar
        </button>
      </div>
    </div>
  )
}

export default GuardarComoPlantilla
