import './config.css'

// Paleta base del tema (14 colores → dos filas parejas). El nombre se muestra en
// "recomendado" en lugar del hash.
const PALETA: { hex: string; nombre: string }[] = [
  { hex: '#e3b341', nombre: 'Dorado' },
  { hex: '#388bfd', nombre: 'Azul' },
  { hex: '#3fb950', nombre: 'Verde' },
  { hex: '#f85149', nombre: 'Rojo' },
  { hex: '#a371f7', nombre: 'Violeta' },
  { hex: '#8b949e', nombre: 'Gris' },
  { hex: '#39c5cf', nombre: 'Cian' },
  { hex: '#f0883e', nombre: 'Naranja' },
  { hex: '#db61a2', nombre: 'Magenta' },
  { hex: '#ff7b72', nombre: 'Salmón' },
  { hex: '#7ee787', nombre: 'Verde claro' },
  { hex: '#79c0ff', nombre: 'Celeste' },
  { hex: '#d2a8ff', nombre: 'Lila' },
  { hex: '#ffffff', nombre: 'Blanco' },
]

const NOMBRE_POR_HEX = new Map(PALETA.map(({ hex, nombre }) => [hex.toLowerCase(), nombre]))

// Nombre del color para mostrar; si no está en la paleta, cae al hash.
export function nombreColor(hex: string): string {
  return NOMBRE_POR_HEX.get(hex.toLowerCase()) ?? hex
}

interface Props {
  valor: string
  alCambiar: (color: string) => void
}

function SelectorColor({ valor, alCambiar }: Props) {
  return (
    <div className="selector-color">
      {PALETA.map(({ hex, nombre }) => (
        <button
          key={hex}
          type="button"
          title={nombre}
          className={hex.toLowerCase() === valor.toLowerCase() ? 'muestra activa' : 'muestra'}
          style={{ backgroundColor: hex }}
          onClick={() => alCambiar(hex)}
        />
      ))}
    </div>
  )
}

export default SelectorColor
