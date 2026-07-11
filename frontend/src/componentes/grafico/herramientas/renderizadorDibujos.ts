import type {
  IChartApi,
  IPriceLine,
  ISeriesApi,
  ISeriesPrimitive,
  SeriesType,
  Time,
} from 'lightweight-charts'
import type { Dibujo } from '../../../api/cliente'
import { aLineStyle } from '../../../contextos/EstilosContext'
import { PrimitivaTendencia } from './primitivaTendencia'
import { PrimitivaFibonacci, NIVELES_FIBONACCI } from './primitivaFibonacci'
import { PrimitivaMedicion } from './primitivaMedicion'
import { RECOMENDADO_DIBUJO, estiloDeDibujo, type EstiloDibujo } from './estiloDibujo'

const COLOR_SELECCION = '#ffffff'
const TOLERANCIA_CLICK = 6 // px de margen para detectar el dibujo tocado

interface Punto {
  ts: number
  precio: number
}

// Primitivas de dos puntos (tendencia, fibonacci, medición): comparten la
// interfaz para crearlas, actualizarlas y previsualizarlas de forma uniforme.
interface PrimitivaDibujo extends ISeriesPrimitive {
  actualizar(p1: Punto, p2: Punto): void
  actualizarPixel(x: number, y: number): void
  actualizarEstilo(estilo: EstiloDibujo): void
  seleccionar(sel: boolean): void
}

function distanciaASegmento(
  px: number, py: number,
  ax: number, ay: number,
  bx: number, by: number,
): number {
  const dx = bx - ax
  const dy = by - ay
  const largo2 = dx * dx + dy * dy
  if (largo2 === 0) return Math.hypot(px - ax, py - ay)
  let t = ((px - ax) * dx + (py - ay) * dy) / largo2
  t = Math.max(0, Math.min(1, t))
  return Math.hypot(px - (ax + t * dx), py - (ay + t * dy))
}

interface LineaActiva {
  dibujoId: number
  priceLine: IPriceLine
}

interface PrimitivaActiva {
  dibujoId: number
  primitiva: PrimitivaDibujo
}

export interface RenderizadorDibujos {
  sincronizar(dibujos: Dibujo[]): void
  previsualizar(tipo: string, p1: Punto, x: number, y: number, estilo?: EstiloDibujo): void
  limpiarPrevisualizacion(): void
  dibujoEn(x: number, y: number): number | null
  seleccionar(id: number | null): void
  destruir(): void
}

export function crearRenderizadorDibujos(
  chart: IChartApi,
  serie: ISeriesApi<SeriesType>,
  _alActualizar: (id: number, datos: Record<string, unknown>) => void,
  _alEliminar: (id: number) => void,
): RenderizadorDibujos {
  const lineas = new Map<number, LineaActiva>()
  const primitivas = new Map<number, PrimitivaActiva>()
  let previa: PrimitivaDibujo | null = null
  let previaTipo: string | null = null
  let dibujosActuales: Dibujo[] = []
  let seleccionado: number | null = null

  function crearPrimitiva(
    tipo: string,
    p1: Punto,
    p2: Punto,
    punteada: boolean,
    estilo: EstiloDibujo,
  ): PrimitivaDibujo | null {
    if (tipo === 'tendencia') return new PrimitivaTendencia(chart, serie, p1, p2, punteada, estilo)
    if (tipo === 'fibonacci') return new PrimitivaFibonacci(chart, serie, p1, p2, punteada, estilo)
    if (tipo === 'medicion') return new PrimitivaMedicion(chart, serie, p1, p2, punteada, estilo)
    return null
  }

  function sincronizar(dibujos: Dibujo[]) {
    dibujosActuales = dibujos
    if (seleccionado != null && !dibujos.some((d) => d.id === seleccionado)) {
      seleccionado = null
    }
    const idsActuales = new Set(dibujos.map((d) => d.id))

    for (const [id, linea] of lineas) {
      if (!idsActuales.has(id)) {
        try { serie.removePriceLine(linea.priceLine) } catch { /* */ }
        lineas.delete(id)
      }
    }
    for (const [id, p] of primitivas) {
      if (!idsActuales.has(id)) {
        try { serie.detachPrimitive(p.primitiva) } catch { /* */ }
        primitivas.delete(id)
      }
    }

    for (const dibujo of dibujos) {
      if (dibujo.tipo === 'horizontal') sincronizarHorizontal(dibujo)
      else sincronizarPrimitiva(dibujo)
    }

    // Reaplicar el resaltado: la horizontal pierde estilo al re-aplicar opciones
    // y una primitiva recreada nace sin seleccionar.
    if (seleccionado != null) aplicarSeleccion(seleccionado, true)
  }

  function sincronizarHorizontal(dibujo: Dibujo) {
    const precio = dibujo.datos.precio as number
    const estilo = estiloDeDibujo(dibujo.datos)
    const opciones = {
      price: precio,
      color: estilo.color ?? RECOMENDADO_DIBUJO.color!,
      lineWidth: (estilo.ancho ?? 1) as 1 | 2 | 3 | 4,
      lineStyle: aLineStyle(estilo.tipoLinea),
    }
    const existente = lineas.get(dibujo.id)
    if (existente) {
      existente.priceLine.applyOptions(opciones)
      return
    }
    const priceLine = serie.createPriceLine({
      ...opciones,
      axisLabelVisible: true,
      title: '',
    })
    lineas.set(dibujo.id, { dibujoId: dibujo.id, priceLine })
  }

  function sincronizarPrimitiva(dibujo: Dibujo) {
    const p1 = dibujo.datos.p1 as Punto
    const p2 = dibujo.datos.p2 as Punto
    if (!p1 || !p2) return
    const estilo = estiloDeDibujo(dibujo.datos)
    const existente = primitivas.get(dibujo.id)
    if (existente) {
      existente.primitiva.actualizarEstilo(estilo)
      existente.primitiva.actualizar(p1, p2)
      return
    }
    const primitiva = crearPrimitiva(dibujo.tipo, p1, p2, false, estilo)
    if (!primitiva) return
    serie.attachPrimitive(primitiva)
    primitivas.set(dibujo.id, { dibujoId: dibujo.id, primitiva })
  }

  function previsualizar(tipo: string, p1: Punto, x: number, y: number, estilo: EstiloDibujo = {}) {
    if (!previa || previaTipo !== tipo) {
      limpiarPrevisualizacion()
      const primitiva = crearPrimitiva(tipo, p1, p1, true, estilo)
      if (!primitiva) return
      previa = primitiva
      previaTipo = tipo
      serie.attachPrimitive(previa)
    }
    previa.actualizarPixel(x, y)
  }

  function limpiarPrevisualizacion() {
    if (previa) {
      try { serie.detachPrimitive(previa) } catch { /* */ }
      previa = null
      previaTipo = null
    }
  }

  // Devuelve el id del dibujo bajo el píxel (x, y), o null. Recorre de arriba
  // (último dibujado) hacia abajo para priorizar el que está al frente.
  function dibujoEn(x: number, y: number): number | null {
    for (let i = dibujosActuales.length - 1; i >= 0; i--) {
      if (impacta(dibujosActuales[i], x, y)) return dibujosActuales[i].id
    }
    return null
  }

  function impacta(d: Dibujo, x: number, y: number): boolean {
    if (d.tipo === 'horizontal') {
      const yp = serie.priceToCoordinate(d.datos.precio as number)
      return yp != null && Math.abs(yp - y) <= TOLERANCIA_CLICK
    }

    const p1 = d.datos.p1 as Punto | undefined
    const p2 = d.datos.p2 as Punto | undefined
    if (!p1 || !p2) return false
    const ts = chart.timeScale()
    const x1 = ts.timeToCoordinate(p1.ts as unknown as Time)
    const x2 = ts.timeToCoordinate(p2.ts as unknown as Time)
    if (x1 == null || x2 == null) return false
    const izq = Math.min(x1, x2)
    const der = Math.max(x1, x2)

    if (d.tipo === 'tendencia') {
      const y1 = serie.priceToCoordinate(p1.precio)
      const y2 = serie.priceToCoordinate(p2.precio)
      if (y1 == null || y2 == null) return false
      return distanciaASegmento(x, y, x1, y1, x2, y2) <= TOLERANCIA_CLICK
    }

    if (d.tipo === 'fibonacci') {
      if (x < izq - TOLERANCIA_CLICK || x > der + TOLERANCIA_CLICK) return false
      for (const nivel of NIVELES_FIBONACCI) {
        const precio = p1.precio + (p2.precio - p1.precio) * nivel
        const yp = serie.priceToCoordinate(precio)
        if (yp != null && Math.abs(yp - y) <= TOLERANCIA_CLICK) return true
      }
      return false
    }

    if (d.tipo === 'medicion') {
      const y1 = serie.priceToCoordinate(p1.precio)
      const y2 = serie.priceToCoordinate(p2.precio)
      if (y1 == null || y2 == null) return false
      const arr = Math.min(y1, y2)
      const aba = Math.max(y1, y2)
      return (
        x >= izq - TOLERANCIA_CLICK && x <= der + TOLERANCIA_CLICK &&
        y >= arr - TOLERANCIA_CLICK && y <= aba + TOLERANCIA_CLICK
      )
    }

    return false
  }

  function aplicarSeleccion(id: number, sel: boolean) {
    const linea = lineas.get(id)
    if (linea) {
      const d = dibujosActuales.find((x) => x.id === id)
      const estilo = d ? estiloDeDibujo(d.datos) : RECOMENDADO_DIBUJO
      const ancho = (estilo.ancho ?? 1) as 1 | 2 | 3 | 4
      linea.priceLine.applyOptions({
        color: sel ? COLOR_SELECCION : estilo.color ?? RECOMENDADO_DIBUJO.color!,
        lineWidth: (sel ? Math.min(ancho + 1, 4) : ancho) as 1 | 2 | 3 | 4,
      })
      return
    }
    const p = primitivas.get(id)
    if (p) p.primitiva.seleccionar(sel)
  }

  function seleccionar(id: number | null) {
    if (seleccionado === id) return
    if (seleccionado != null) aplicarSeleccion(seleccionado, false)
    seleccionado = id
    if (seleccionado != null) aplicarSeleccion(seleccionado, true)
  }

  function destruir() {
    limpiarPrevisualizacion()
    for (const linea of lineas.values()) {
      try { serie.removePriceLine(linea.priceLine) } catch { /* */ }
    }
    for (const p of primitivas.values()) {
      try { serie.detachPrimitive(p.primitiva) } catch { /* */ }
    }
    lineas.clear()
    primitivas.clear()
  }

  return { sincronizar, previsualizar, limpiarPrevisualizacion, dibujoEn, seleccionar, destruir }
}
