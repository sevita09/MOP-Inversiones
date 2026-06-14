import type {
  Moneda,
  Paneles,
  Precios,
  RespuestaDolar,
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

export function obtenerTickers(): Promise<Paneles> {
  return obtenerJson<Paneles>('/api/tickers')
}

export function obtenerPrecios(moneda: Moneda): Promise<Precios> {
  return obtenerJson<Precios>(`/api/precios?moneda=${moneda}`)
}
