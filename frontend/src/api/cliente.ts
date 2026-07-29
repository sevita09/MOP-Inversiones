import type {
  BacktestRapidoPeticion,
  Bot,
  BotNuevo,
  Categoria,
  EstadoOptimizacion,
  MetricaOptimizacion,
  ParametroOptimizacion,
  ResultadoBacktest,
  Plantilla,
  PlantillaNueva,
  PresetRiesgo,
  ReglasBot,
  RiesgoBot,
  RespuestaSenales,
  Comisiones,
  Realizado,
  Rendimiento,
  TasaVigente,
  TipoOperacion,
  LotesDeTicker,
  OperacionesDeTicker,
  Split,
  SplitNuevo,
  Tenencias,
  Transaccion,
  TransaccionNueva,
  RespuestaPreview,
  TemporalidadBot,
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

// --- Bots ---

export function obtenerBots(): Promise<Bot[]> {
  return obtenerJson<Bot[]>('/api/bots')
}

export function obtenerBot(id: number): Promise<Bot> {
  return obtenerJson<Bot>('/api/bots/' + id)
}

export function crearBot(datos: BotNuevo): Promise<Bot> {
  return fetchJson<Bot>('/api/bots', { method: 'POST', body: JSON.stringify(datos) })
}

export function editarBot(
  id: number,
  cambios: Partial<BotNuevo> & { activo?: boolean },
): Promise<Bot> {
  return fetchJson<Bot>('/api/bots/' + id, {
    method: 'PUT',
    body: JSON.stringify(cambios),
  })
}

export function eliminarBot(id: number): Promise<void> {
  return fetchJson('/api/bots/' + id, { method: 'DELETE' })
}

export function duplicarBot(id: number): Promise<Bot> {
  return fetchJson<Bot>('/api/bots/' + id + '/duplicar', { method: 'POST' })
}

export function obtenerPlantillas(): Promise<Plantilla[]> {
  return obtenerJson<Plantilla[]>('/api/plantillas')
}

export function crearPlantilla(datos: PlantillaNueva): Promise<Plantilla> {
  return fetchJson<Plantilla>('/api/plantillas', {
    method: 'POST',
    body: JSON.stringify(datos),
  })
}

export function eliminarPlantilla(id: number): Promise<void> {
  return fetchJson('/api/plantillas/' + id, { method: 'DELETE' })
}

// --- Backtest ---

export function obtenerBacktest(
  id: number,
  desde?: number,
  hasta?: number,
): Promise<ResultadoBacktest> {
  const parametros = new URLSearchParams()
  if (desde) parametros.set('desde', String(desde))
  if (hasta) parametros.set('hasta', String(hasta))
  const cola = parametros.toString() ? `?${parametros}` : ''
  return obtenerJson<ResultadoBacktest>(`/api/bots/${id}/backtest${cola}`)
}

export function backtestRapido(datos: BacktestRapidoPeticion): Promise<ResultadoBacktest> {
  return fetchJson<ResultadoBacktest>('/api/bots/backtest_rapido', {
    method: 'POST',
    body: JSON.stringify(datos),
  })
}

// --- Cartera ---

export function obtenerTransacciones(ticker?: string): Promise<Transaccion[]> {
  const cola = ticker ? `?ticker=${ticker}` : ''
  return obtenerJson<Transaccion[]>(`/api/cartera/transacciones${cola}`)
}

export function crearTransaccion(datos: TransaccionNueva): Promise<Transaccion> {
  return fetchJson<Transaccion>('/api/cartera/transacciones', {
    method: 'POST',
    body: JSON.stringify(datos),
  })
}

export function editarTransaccion(
  id: number,
  cambios: Partial<TransaccionNueva>,
): Promise<Transaccion> {
  return fetchJson<Transaccion>('/api/cartera/transacciones/' + id, {
    method: 'PUT',
    body: JSON.stringify(cambios),
  })
}

export function eliminarTransaccion(id: number): Promise<void> {
  return fetchJson('/api/cartera/transacciones/' + id, { method: 'DELETE' })
}

export function obtenerPrecioSugerido(
  ticker: string,
  fecha: string,
): Promise<{ ticker: string; fecha: string; precio: number | null }> {
  const parametros = new URLSearchParams({ ticker, fecha })
  return obtenerJson<{ ticker: string; fecha: string; precio: number | null }>(
    `/api/cartera/precio_sugerido?${parametros}`,
  )
}

export function obtenerLotes(ticker: string, moneda: Moneda): Promise<LotesDeTicker> {
  const parametros = new URLSearchParams({ ticker, moneda })
  return obtenerJson<LotesDeTicker>(`/api/cartera/lotes?${parametros}`)
}

export function obtenerOperacionesGrafico(
  ticker: string,
  moneda: Moneda,
): Promise<OperacionesDeTicker> {
  const parametros = new URLSearchParams({ ticker, moneda })
  return obtenerJson<OperacionesDeTicker>(`/api/cartera/operaciones_grafico?${parametros}`)
}

export function obtenerSplits(ticker?: string): Promise<Split[]> {
  const cola = ticker ? `?ticker=${ticker}` : ''
  return obtenerJson<Split[]>(`/api/cartera/splits${cola}`)
}

export function crearSplit(datos: SplitNuevo): Promise<Split> {
  return fetchJson<Split>('/api/cartera/splits', {
    method: 'POST',
    body: JSON.stringify(datos),
  })
}

export function eliminarSplit(id: number): Promise<void> {
  return fetchJson('/api/cartera/splits/' + id, { method: 'DELETE' })
}

export function obtenerTenencias(): Promise<Tenencias> {
  return obtenerJson<Tenencias>('/api/cartera/tenencias')
}

export function obtenerRealizado(): Promise<Realizado> {
  return obtenerJson<Realizado>('/api/cartera/realizado')
}

export function obtenerRendimiento(moneda: Moneda, desde?: string): Promise<Rendimiento> {
  const parametros = new URLSearchParams({ moneda })
  if (desde) parametros.set('desde', desde)
  return obtenerJson<Rendimiento>(`/api/cartera/rendimiento?${parametros}`)
}

export function obtenerPapelesEnCartera(): Promise<Record<string, number>> {
  return obtenerJson<Record<string, number>>('/api/cartera/en_cartera')
}

export function obtenerComisiones(): Promise<Comisiones> {
  return obtenerJson<Comisiones>('/api/cartera/comisiones')
}

export function guardarComisiones(datos: Comisiones): Promise<Comisiones> {
  return fetchJson<Comisiones>('/api/cartera/comisiones', {
    method: 'PUT',
    body: JSON.stringify(datos),
  })
}

export function obtenerTasaVigente(
  ticker: string,
  fecha: string,
  tipo: TipoOperacion,
): Promise<TasaVigente> {
  const parametros = new URLSearchParams({ ticker, fecha, tipo })
  return obtenerJson<TasaVigente>(`/api/cartera/tasa_vigente?${parametros}`)
}

// --- Optimizador ---

export function lanzarOptimizacion(
  idBot: number,
  parametros: ParametroOptimizacion[],
  metrica: MetricaOptimizacion,
): Promise<{ lanzada: boolean }> {
  return fetchJson<{ lanzada: boolean }>(`/api/optimizacion/${idBot}`, {
    method: 'POST',
    body: JSON.stringify({ parametros, metrica }),
  })
}

export function obtenerEstadoOptimizacion(): Promise<EstadoOptimizacion> {
  return obtenerJson<EstadoOptimizacion>('/api/optimizacion')
}

// --- Presets de riesgo ---

export function obtenerPresetsRiesgo(): Promise<PresetRiesgo[]> {
  return obtenerJson<PresetRiesgo[]>('/api/riesgo/presets')
}

export function crearPresetRiesgo(nombre: string, riesgo: RiesgoBot): Promise<PresetRiesgo> {
  return fetchJson<PresetRiesgo>('/api/riesgo/presets', {
    method: 'POST',
    body: JSON.stringify({ nombre, riesgo }),
  })
}

export function eliminarPresetRiesgo(id: number): Promise<void> {
  return fetchJson('/api/riesgo/presets/' + id, { method: 'DELETE' })
}

// --- Señales del día ---

export function obtenerSenales(): Promise<RespuestaSenales> {
  return obtenerJson<RespuestaSenales>('/api/senales')
}

export function marcarSenalesVistas(): Promise<{ marcadas: number }> {
  return fetchJson<{ marcadas: number }>('/api/senales/vistas', { method: 'POST' })
}

export function eliminarSenal(id: number): Promise<void> {
  return fetchJson('/api/senales/' + id, { method: 'DELETE' })
}

export function eliminarSenalesVencidas(): Promise<{ eliminadas: number }> {
  return fetchJson<{ eliminadas: number }>('/api/senales/eliminar_vencidas', { method: 'POST' })
}

export function previewBot(
  ticker: string,
  temporalidad: TemporalidadBot,
  moneda: Moneda,
  reglas: ReglasBot,
): Promise<RespuestaPreview> {
  return fetchJson<RespuestaPreview>('/api/bots/preview', {
    method: 'POST',
    body: JSON.stringify({ ticker, temporalidad, moneda, reglas }),
  })
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
