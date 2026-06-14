import { useEffect, useState } from 'react'
import { urlLogo } from '../api/cliente'
import './LogoTicker.css'

interface Props {
  ticker: string
  tamano?: number
}

function esTickerDolar(ticker: string): boolean {
  return ticker.startsWith('DOLAR')
}

function iniciales(ticker: string): string {
  return ticker.slice(0, 2)
}

// Color estable por ticker (mismo papel → mismo color)
function colorDesdeTicker(ticker: string): string {
  let acumulado = 0
  for (const caracter of ticker) {
    acumulado = caracter.charCodeAt(0) + ((acumulado << 5) - acumulado)
  }
  return `hsl(${Math.abs(acumulado) % 360} 45% 38%)`
}

function LogoTicker({ ticker, tamano = 20 }: Props) {
  const [falló, setFalló] = useState(false)
  const estilo = { width: tamano, height: tamano, fontSize: tamano * 0.42 }

  // Reintentar la imagen cuando cambia el ticker
  useEffect(() => {
    setFalló(false)
  }, [ticker])

  if (esTickerDolar(ticker)) {
    return (
      <span className="logo-ticker logo-dolar" style={estilo}>
        $
      </span>
    )
  }

  if (falló) {
    return (
      <span
        className="logo-ticker logo-iniciales"
        style={{ ...estilo, backgroundColor: colorDesdeTicker(ticker) }}
      >
        {iniciales(ticker)}
      </span>
    )
  }

  return (
    <img
      className="logo-ticker"
      style={estilo}
      src={urlLogo(ticker)}
      alt=""
      onError={() => setFalló(true)}
    />
  )
}

export default LogoTicker
