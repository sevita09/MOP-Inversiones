import './BotonPantallaCompleta.css'

interface Props {
  activa: boolean
  alAlternar: () => void
}

function BotonPantallaCompleta({ activa, alAlternar }: Props) {
  return (
    <button
      type="button"
      className="boton-pantalla"
      title={activa ? 'Salir de pantalla completa' : 'Pantalla completa'}
      onClick={alAlternar}
    >
      {activa ? (
        <svg width="15" height="15" viewBox="0 0 15 15" fill="none" stroke="currentColor" strokeWidth="1.5">
          <path d="M6 1 V6 H1 M14 6 H9 V1 M9 14 V9 H14 M1 9 H6 V14" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      ) : (
        <svg width="15" height="15" viewBox="0 0 15 15" fill="none" stroke="currentColor" strokeWidth="1.5">
          <path d="M1 5 V1 H5 M10 1 H14 V5 M14 10 V14 H10 M5 14 H1 V10" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      )}
    </button>
  )
}

export default BotonPantallaCompleta
