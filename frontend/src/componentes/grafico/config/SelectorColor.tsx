import './config.css'

// Paleta base del tema (los indicadores suelen usar estos)
const PRESETS = [
  '#e3b341', '#388bfd', '#3fb950', '#f85149', '#a371f7',
  '#8b949e', '#39c5cf', '#f0883e', '#ffffff',
]

interface Props {
  valor: string
  alCambiar: (color: string) => void
}

function SelectorColor({ valor, alCambiar }: Props) {
  return (
    <div className="selector-color">
      {PRESETS.map((color) => (
        <button
          key={color}
          type="button"
          className={color.toLowerCase() === valor.toLowerCase() ? 'muestra activa' : 'muestra'}
          style={{ backgroundColor: color }}
          onClick={() => alCambiar(color)}
        />
      ))}
      <label className="muestra-custom" title="Color personalizado">
        <input type="color" value={valor} onChange={(e) => alCambiar(e.target.value)} />
      </label>
    </div>
  )
}

export default SelectorColor
