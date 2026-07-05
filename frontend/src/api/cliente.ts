import type {
  EstadoActualizacion,
  Moneda,
  Paneles,
  Precios,
  RespuestaDolar,
  RespuestaIndicadores,
  RespuestaVelas,
  Temporalidad,
} from './tipos'

const URL_BASE = 'http://localhost:8000'

export async function obtenerJson<T>(ruta: string): Promise<T> {
  const respuesta = await fetch(`${URL_BASE}${ruta}`)
  if (!respuesta.ok) {
    throw new Error(`Error ${respuesta.status} en ${ruta}`)
  }
  return respuesta.json() as Promise<T>
}

export function obtenerVelas(
  ticker: string,
  temporalidad: Temporalidad,
  moneda: Moneda,
): Promise<RespuestaVelas> {
  const parametros = new URLSearchParams({ ticker, temporalidad, moneda })
  return obtenerJson<RespuestaVelas>(`/api/velas?${parametros}`)
}

export function obtenerDolar(): Promise<RespuestaDolar> {
  return obtenerJson<RespuestaDolar>('/api/dolar')
}

export function obtenerActualizacion(): Promise<EstadoActualizacion> {
  return obtenerJson<EstadoActualizacion>('/api/actualizacion')
}

export function obtenerIndicadores(
  ticker: string,
  temporalidad: Temporalidad,
  moneda: Moneda,
  incluir: string,
): Promise<RespuestaIndicadores> {
  const parametros = new URLSearchParams({ ticker, temporalidad, moneda, incluir })
  return obtenerJson<RespuestaIndicadores>(`/api/indicadores?${parametros}`)
}

export function urlLogo(ticker: string): string {
  return `${URL_BASE}/api/logo/${ticker}`
}

export function obtenerTickers(): Promise<Paneles> {
  return obtenerJson<Paneles>('/api/tickers')
}

export function obtenerPrecios(moneda: Moneda): Promise<Precios> {
  return obtenerJson<Precios>(`/api/precios?moneda=${moneda}`)
}

// --- Dibujos ---

export interface Dibujo {
  id: number
  ticker: string
  tipo: string
  datos: Record<string, unknown>
}

export function obtenerDibujos(ticker: string): Promise<Dibujo[]> {
  return obtenerJson<Dibujo[]>(`/api/dibujos?ticker=${ticker}`)
}

async function fetchJson<T>(ruta: string, opciones: RequestInit): Promise<T> {
  const resp = await fetch(`${URL_BASE}${ruta}`, {
    ...opciones,
    headers: { 'Content-Type': 'application/json', ...opciones.headers },
  })
  if (!resp.ok) throw new Error(`Error ${resp.status} en ${ruta}`)
  return resp.json() as Promise<T>
}

export function crearDibujo(ticker: string, tipo: string, datos: Record<string, unknown>): Promise<Dibujo> {
  return fetchJson<Dibujo>('/api/dibujos', {
    method: 'POST',
    body: JSON.stringify({ ticker, tipo, datos }),
  })
}

export function actualizarDibujo(id: number, datos: Record<string, unknown>): Promise<void> {
  return fetchJson('/api/dibujos/' + id, {
    method: 'PUT',
    body: JSON.stringify({ datos }),
  })
}

export function eliminarDibujo(id: number): Promise<void> {
  return fetchJson('/api/dibujos/' + id, { method: 'DELETE' })
}

// --- Niveles de swing (soporte/resistencia) ---

export interface NivelSwing {
  precio: number
  tipo: 'soporte' | 'resistencia' | 'mixto'
  contactos: number
  origen: Temporalidad
  ultimo_ts: number
}

export function obtenerNivelesSwing(
  ticker: string,
  temporalidad: Temporalidad,
  moneda: Moneda,
): Promise<{ niveles: NivelSwing[] }> {
  const parametros = new URLSearchParams({ ticker, temporalidad, moneda })
  return obtenerJson<{ niveles: NivelSwing[] }>(`/api/niveles_swing?${parametros}`)
}
