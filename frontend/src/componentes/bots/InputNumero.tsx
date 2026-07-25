import { useEffect, useState } from 'react'
import './InputNumero.css'

interface Props {
  valor: number | null
  alCambiar: (valor: number | null) => void
  prefijo?: string
  sufijo?: string
  placeholder?: string
  miles?: boolean // separador de miles (para el capital)
  disabled?: boolean
}

function formatear(valor: number | null, miles?: boolean): string {
  if (valor === null || valor === undefined || Number.isNaN(valor)) return ''
  return miles ? valor.toLocaleString('es-AR') : String(valor)
}

function parsear(texto: string, miles?: boolean): number | null {
  if (miles) {
    const digitos = texto.replace(/\D/g, '')
    return digitos === '' ? null : parseInt(digitos, 10)
  }
  const limpio = texto.replace(/[^\d.]/g, '')
  if (limpio === '' || limpio === '.') return null
  const num = parseFloat(limpio)
  return Number.isNaN(num) ? null : num
}

/** Input numérico sin spinners, con afijo interno (%, $, ×) y formateo de miles.
 *  Guarda un buffer de texto propio para no romper la escritura de decimales. */
function InputNumero({
  valor,
  alCambiar,
  prefijo,
  sufijo,
  placeholder = '—',
  miles,
  disabled,
}: Props) {
  const [texto, setTexto] = useState(() => formatear(valor, miles))

  // Resincronizar cuando el valor cambia desde afuera (preset, plantilla, reset)
  useEffect(() => {
    if (parsear(texto, miles) !== valor) setTexto(formatear(valor, miles))
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [valor])

  const alEscribir = (bruto: string) => {
    const num = parsear(bruto, miles)
    // Con miles se reformatea al vuelo (entero); en decimales se deja tal cual
    setTexto(miles ? formatear(num, true) : bruto.replace(/[^\d.]/g, ''))
    alCambiar(num)
  }

  const clases = [
    'input-numero',
    prefijo ? 'con-prefijo' : '',
    sufijo ? 'con-sufijo' : '',
    disabled ? 'deshabilitado' : '',
  ]
    .filter(Boolean)
    .join(' ')

  return (
    <div className={clases}>
      {prefijo && <span className="afijo-numero prefijo">{prefijo}</span>}
      <input
        type="text"
        inputMode={miles ? 'numeric' : 'decimal'}
        placeholder={placeholder}
        value={texto}
        disabled={disabled}
        onChange={(evento) => alEscribir(evento.target.value)}
      />
      {sufijo && <span className="afijo-numero sufijo">{sufijo}</span>}
    </div>
  )
}

export default InputNumero
