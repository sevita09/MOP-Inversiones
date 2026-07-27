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
  if (!miles) return String(valor)
  return valor.toLocaleString('es-AR', { maximumFractionDigits: 2 })
}

/** Interpreta el formato argentino: el punto separa miles y la coma decimales.
 *  Así pegar "22.746.810,66" del resumen del broker da 22746810.66 y no
 *  2274681066 (que es lo que pasaba tratando el punto como ruido). */
function parsear(texto: string, miles?: boolean): number | null {
  if (miles) {
    const [entero, decimal] = texto.split(',')
    const digitos = (entero ?? '').replace(/\D/g, '')
    const decimales = (decimal ?? '').replace(/\D/g, '').slice(0, 2)
    if (digitos === '' && decimales === '') return null
    return parseFloat(`${digitos || '0'}.${decimales || '0'}`)
  }
  const limpio = texto.replace(',', '.').replace(/[^\d.]/g, '')
  if (limpio === '' || limpio === '.') return null
  const num = parseFloat(limpio)
  return Number.isNaN(num) ? null : num
}

/** Reformatea mientras se escribe sin romper los decimales a medio tipear:
 *  agrupa la parte entera y deja la decimal tal cual la va poniendo el usuario. */
function formatearMientrasEscribe(texto: string): string {
  const [entero, decimal] = texto.split(',')
  const digitos = (entero ?? '').replace(/\D/g, '')
  const agrupado = digitos === '' ? '' : parseInt(digitos, 10).toLocaleString('es-AR')
  if (decimal === undefined) return agrupado
  return `${agrupado},${decimal.replace(/\D/g, '').slice(0, 2)}`
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
    setTexto(miles ? formatearMientrasEscribe(bruto) : bruto.replace(/[^\d.,]/g, ''))
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
