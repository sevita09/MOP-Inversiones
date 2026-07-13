import type { Vela } from '../../api/tipos'

// Un nivel del perfil: precio central del bin y el volumen acumulado ahí, separado
// entre velas alcistas (sube: cierre ≥ apertura) y bajistas (baja).
export interface BinVPVR {
  precio: number
  volumenSube: number
  volumenBaja: number
}

export interface PerfilVPVR {
  bins: BinVPVR[] // de abajo (min) hacia arriba (max)
  pocIndice: number // índice del bin con más volumen total (Point of Control)
  maxVolumen: number // volumen total del bin más cargado
  min: number // borde inferior del rango de precios
  paso: number // alto de cada bin en precio
}

// Perfil de volumen del rango de precios de `velas`: N bins entre min(low) y
// max(high); el volumen de cada vela se reparte en partes iguales entre los bins
// que abarca su [low, high] (así el total de volumen se conserva), separando alcista
// de bajista. El POC es el bin de mayor volumen total. Cálculo puro en el frontend.
export function calcularVPVR(velas: Vela[], numBins = 24): PerfilVPVR | null {
  if (velas.length === 0 || numBins < 1) return null

  let min = Infinity
  let max = -Infinity
  for (const v of velas) {
    if (v.minimo < min) min = v.minimo
    if (v.maximo > max) max = v.maximo
  }
  if (!isFinite(min) || !isFinite(max)) return null

  const degenerado = max <= min
  const paso = degenerado ? 0 : (max - min) / numBins
  const n = degenerado ? 1 : numBins
  const sube = new Array<number>(n).fill(0)
  const baja = new Array<number>(n).fill(0)
  const binDe = (precio: number) =>
    degenerado ? 0 : Math.min(numBins - 1, Math.max(0, Math.floor((precio - min) / paso)))

  for (const v of velas) {
    const lo = binDe(v.minimo)
    const hi = binDe(v.maximo)
    const porBin = v.volumen / (hi - lo + 1)
    const destino = v.cierre >= v.apertura ? sube : baja
    for (let b = lo; b <= hi; b++) destino[b] += porBin
  }

  let pocIndice = 0
  for (let b = 1; b < n; b++) if (sube[b] + baja[b] > sube[pocIndice] + baja[pocIndice]) pocIndice = b

  const bins: BinVPVR[] = sube.map((volumenSube, b) => ({
    precio: degenerado ? min : min + paso * (b + 0.5),
    volumenSube,
    volumenBaja: baja[b],
  }))
  return { bins, pocIndice, maxVolumen: sube[pocIndice] + baja[pocIndice], min, paso }
}
