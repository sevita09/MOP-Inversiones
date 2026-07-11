import type { TipoMedia } from '../../contextos/EmasExtraContext'

// Media móvil del cierre, alineada al mismo índice. Replica el backend:
//  - exponencial: ewm con adjust=False (arranca en el primer valor, sin warmup nulo)
//  - simple: promedio rolling (los primeros período−1 quedan en null)
export function mediaMovil(
  cierres: number[],
  periodo: number,
  tipo: TipoMedia,
): (number | null)[] {
  if (periodo < 1 || cierres.length === 0) return cierres.map(() => null)

  if (tipo === 'simple') {
    const salida: (number | null)[] = []
    let suma = 0
    for (let i = 0; i < cierres.length; i++) {
      suma += cierres[i]
      if (i >= periodo) suma -= cierres[i - periodo]
      salida.push(i >= periodo - 1 ? suma / periodo : null)
    }
    return salida
  }

  const alfa = 2 / (periodo + 1)
  const salida: (number | null)[] = [cierres[0]]
  for (let i = 1; i < cierres.length; i++) {
    salida.push(alfa * cierres[i] + (1 - alfa) * (salida[i - 1] as number))
  }
  return salida
}
