import './config.css'

interface Props {
  titulo: string
  alTocar: () => void
}

/** Tuerca chica para abrir la configuración de un indicador. */
function BotonTuerca({ titulo, alTocar }: Props) {
  return (
    <button type="button" className="boton-tuerca" title={titulo} onClick={alTocar}>
      ⚙
    </button>
  )
}

export default BotonTuerca
