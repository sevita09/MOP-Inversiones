import type {
  Categoria,
  EstadoActualizacion,
  InfoAdr,
  Moneda,
  Paneles,
  Precios,
  RespuestaDolar,
  RespuestaIndicadores,
  RespuestaVelas,
  Temporalidad,
} from './tipos'

// En desarrollo (Vite, puerto 5173) la API vive en el 8001 — puerto propio del
// modo web, para no chocar con la app instalada (8000) ni con MOP Dev (8100).
// Compilado, el backend sirve el frontend desde el mismo origen.
const URL_BASE = import.meta.env.DEV ? 'http://localhost:8001' : ''

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

export function obtenerAdr(ticker: string): Promise<{ adr: InfoAdr | null }> {
  return obtenerJson<{ adr: InfoAdr | null }>(`/api/adr?ticker=${ticker}`)
}

export function obtenerActualizacion(): Promise<EstadoActualizacion> {
  return obtenerJson<EstadoActualizacion>('/api/actualizacion')
}

export function obtenerVersion(): Promise<{ version: string; canal: string }> {
  return obtenerJson<{ version: string; canal: string }>('/api/version')
}

export function obtenerEstadoSync(): Promise<{ en_curso: boolean; ultima_sync: string | null }> {
  return obtenerJson<{ en_curso: boolean; ultima_sync: string | null }>('/api/sync')
}

export function instalarActualizacion(): Promise<{ instalando: string }> {
  return fetchJson<{ instalando: string }>('/api/actualizacion/instalar', { method: 'POST' })
}

export function obtenerIndicadores(
  ticker: string,
  temporalidad: Temporalidad,
  moneda: Moneda,
  incluir: string,
  params = '',
): Promise<RespuestaIndicadores> {
  const parametros = new URLSearchParams({ ticker, temporalidad, moneda, incluir })
  if (params) parametros.set('params', params)
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

// --- Categorías propias y favoritos ---

export function obtenerCategorias(): Promise<Categoria[]> {
  return obtenerJson<Categoria[]>('/api/categorias')
}

export function crearCategoria(nombre: string): Promise<Categoria> {
  return fetchJson<Categoria>('/api/categorias', {
    method: 'POST',
    body: JSON.stringify({ nombre }),
  })
}

export function eliminarCategoria(id: number): Promise<void> {
  return fetchJson('/api/categorias/' + id, { method: 'DELETE' })
}

export function agregarTickerACategoria(id: number, ticker: string): Promise<void> {
  return fetchJson('/api/categorias/' + id + '/tickers', {
    method: 'POST',
    body: JSON.stringify({ ticker }),
  })
}

export function quitarTickerDeCategoria(id: number, ticker: string): Promise<void> {
  return fetchJson('/api/categorias/' + id + '/tickers/' + ticker, { method: 'DELETE' })
}

export function agregarTickerNuevo(ticker: string, grupo: string): Promise<{ ticker: string }> {
  return fetchJson<{ ticker: string }>('/api/tickers_extra', {
    method: 'POST',
    body: JSON.stringify({ ticker, grupo }),
  })
}

export function obtenerFavoritos(): Promise<{ tickers: string[] }> {
  return obtenerJson<{ tickers: string[] }>('/api/favoritos')
}

export function guardarFavoritos(tickers: string[]): Promise<{ tickers: string[] }> {
  return fetchJson<{ tickers: string[] }>('/api/favoritos', {
    method: 'PUT',
    body: JSON.stringify({ tickers }),
  })
}

export function marcarFavorito(ticker: string): Promise<{ tickers: string[] }> {
  return fetchJson<{ tickers: string[] }>('/api/favoritos/' + ticker, { method: 'POST' })
}

export function desmarcarFavorito(ticker: string): Promise<{ tickers: string[] }> {
  return fetchJson<{ tickers: string[] }>('/api/favoritos/' + ticker, { method: 'DELETE' })
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
