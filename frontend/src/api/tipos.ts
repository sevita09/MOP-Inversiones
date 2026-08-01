export interface EstadoSalud {
  estado: string
  servicio: string
}

export type Temporalidad = 'H' | 'D' | 'S' | 'M'
export type Moneda = 'ARS' | 'USD'
export type TipoGrafico = 'velas' | 'linea' | 'area'
export type EscalaPrecio = 'lineal' | 'log'

export interface Vela {
  ticker: string
  temporalidad: string
  ts: number
  apertura: number
  maximo: number
  minimo: number
  cierre: number
  volumen: number
  es_faltante: number
}

export interface InfoAdr {
  simbolo: string
  ratio: number
}

export interface RespuestaVelas {
  ticker: string
  temporalidad: string
  moneda: Moneda
  velas: Vela[]
  adr: InfoAdr | null
}

export interface Paneles {
  panel_lider: string[]
  panel_general: string[]
  cedears: string[]
  indices: string[]
  cripto: string[]
  dolar: string[]
}

export interface Precio {
  cierre: number
  variacion_pct: number | null
}

export type Precios = Record<string, Precio>

export interface Tasa {
  fecha: string
  tipo: string
  valor: number
}

export interface RespuestaDolar {
  ccl: Tasa | null
  mep: Tasa | null
  oficial: Tasa | null
}

// Cada serie de un indicador; null en las posiciones de warmup (sin valor)
export type SerieIndicador = (number | null)[]

export interface RespuestaIndicadores {
  ticker: string
  temporalidad: string
  moneda: Moneda
  ts: number[]
  indicadores: Record<string, Record<string, SerieIndicador>>
}

export interface EstadoActualizacion {
  actual: string
  ultima: string | null
  hay_nueva: boolean
  url_descarga: string
}

export interface Categoria {
  id: number
  nombre: string
  tickers: string[]
}

// --- Bots ---

export type TemporalidadBot = 'D' | 'S' | 'M'

export interface CapitalBot {
  inicial: number
  porcentaje_por_posicion: number
}

export interface RiesgoBot {
  stop_loss_pct: number | null
  stop_atr_mult: number | null
  take_profit_pct: number | null
  salida_ema_central: boolean
  trailing_pct: number | null
  atr_periodo: number
  sizing_riesgo_pct: number | null
}

export interface PresetRiesgo {
  id: number
  nombre: string
  riesgo: RiesgoBot
}

export interface MetricasBacktest {
  retorno_pct: number
  trades_total: number
  trades_ganados: number
  win_rate_pct: number | null
  drawdown_maximo_pct: number
  sharpe: number | null
  sortino: number | null
  profit_factor: number | null
  expectancy_pct: number | null
  exposicion_pct: number
  racha_maxima_perdidas: number
}

// Resumen cacheado en el bot tras cada backtest
export interface ResumenMetricas {
  desde: number | null
  hasta: number | null
  estrategia: MetricasBacktest
  buy_and_hold_retorno_pct: number
}

export type MotivoSalida = 'senal' | 'stop' | 'trailing' | 'take_profit' | 'fin'

export interface TradeBacktest {
  entrada_ts: number
  entrada_precio: number
  salida_ts: number
  salida_precio: number
  pnl_pct: number
  duracion_dias: number
  gana: boolean
  motivo: MotivoSalida
  abierto_al_final: boolean
}

export interface PuntoCurva {
  ts: number
  capital: number
}

export interface SimulacionBacktest {
  capital_inicial: number
  capital_final: number
  retorno_pct: number
  barras: number
  barras_en_posicion: number
  metricas: MetricasBacktest
  trades: TradeBacktest[]
  curva: PuntoCurva[]
}

export interface ResultadoBacktest {
  ticker: string
  temporalidad: TemporalidadBot
  moneda: Moneda
  desde: number | null
  hasta: number | null
  estrategia: SimulacionBacktest
  buy_and_hold: SimulacionBacktest
}

// --- Cartera ---

export type TipoOperacion = 'compra' | 'venta'

export interface Transaccion {
  id: number
  ticker: string
  tipo: TipoOperacion
  fecha: string // AAAA-MM-DD
  cantidad: number
  precio: number // ARS por unidad (de mercado, sin comisión)
  comision: number
  nota: string
  creado: string
  bruto: number // cantidad × precio
  monto_final: number // lo que pagó o cobró, con la comisión aplicada
  monto_final_usd: number | null
}

// Se carga con `precio` O con `monto_final`: el backend despeja el otro
export interface TransaccionNueva {
  ticker: string
  tipo: TipoOperacion
  fecha: string
  cantidad: number
  precio?: number
  monto_final?: number
  nota?: string
}

// Estructura del boleto: arancel + derechos de mercado, con IVA sobre ambos
export interface Split {
  id: number
  ticker: string
  fecha: string
  ratio: number
  nota: string
  creado: string
}

export interface SplitNuevo {
  ticker: string
  fecha: string
  ratio: number
  nota?: string
}

// Compra abierta de la cartera, para marcarla en el gráfico
export interface LoteAbierto {
  fecha: string
  ts: number | null
  cantidad: number
  precio: number
}

// Una orden ejecutada, ubicada sobre el gráfico del papel (v7.2)
export interface OperacionGrafico {
  id: number
  tipo: TipoOperacion
  fecha: string
  ts: number | null
  cantidad: number
  precio: number
  nota: string
}

export interface OperacionesDeTicker {
  ticker: string
  moneda: Moneda
  operaciones: OperacionGrafico[]
}

export interface LotesDeTicker {
  ticker: string
  moneda: Moneda
  lotes: LoteAbierto[]
  ppc: number | null
  cantidad: number
}

export interface Posicion {
  ticker: string
  cantidad: number
  costo: number
  precio_promedio: number
  precio_actual: number | null
  valor_actual: number | null
  pnl: number | null
  pnl_pct: number | null
  desde: string
  peso_pct: number | null
  valor_usd: number | null
  pnl_usd: number | null
}

export interface TotalesCartera {
  costo: number
  valor_actual: number
  pnl: number
  pnl_pct: number | null
  valor_usd: number | null
  pnl_usd: number | null
  tasa_ccl: number | null
}

export interface Tenencias {
  posiciones: Posicion[]
  totales: TotalesCartera
}

// --- Rendimiento (v7.1) ---

export interface VentaRealizada {
  id: number
  ticker: string
  fecha: string
  cantidad: number
  precio: number
  ingreso: number
  costo: number
  ingreso_usd: number | null
  costo_usd: number | null
  pnl: number
  pnl_pct: number | null
  pnl_usd: number | null
  pnl_usd_pct: number | null
  desde: string | null
}

export interface RealizadoDePapel {
  ticker: string
  operaciones: number
  cantidad: number
  costo: number
  ingreso: number
  costo_usd: number | null
  ingreso_usd: number | null
  pnl: number
  pnl_pct: number | null
  pnl_usd: number | null
  pnl_usd_pct: number | null
  ventas: VentaRealizada[]
}

export interface Realizado {
  papeles: RealizadoDePapel[]
  totales: {
    operaciones: number
    costo: number
    ingreso: number
    costo_usd: number | null
    ingreso_usd: number | null
    pnl: number
    pnl_pct: number | null
    pnl_usd: number | null
    pnl_usd_pct: number | null
  }
}

export interface Rendimiento {
  moneda: Moneda
  fechas: string[]
  /** Cartera en base 100: solo rendimiento, sin el ruido de los aportes */
  cartera: number[]
  /** `inflacion` solo viene en la vista en pesos */
  benchmarks: {
    mep: (number | null)[]
    dolar: (number | null)[]
    mercado: (number | null)[]
    inflacion?: (number | null)[]
  }
  valores: number[]
  totales: {
    desde: string
    hasta: string
    twr_pct: number | null
    valor_actual: number
    aportado_neto: number
    ganancia: number
    /** Cuánto hizo cada benchmark en el período, por clave */
    variaciones: Record<string, number | null>
    /** Puntos porcentuales que le sacó la cartera a cada uno */
    contra: Record<string, number | null>
    mercado_pct: number | null
    inflacion_pct: number | null
    contra_mercado: number | null
    contra_inflacion: number | null
  }
}

// --- What-if (v7.3) ---

export interface ResultadoVenta {
  fecha: string
  precio: number
  ingreso: number
  costo: number
  pnl: number
  pnl_pct: number | null
}

export interface Escenario extends ResultadoVenta {
  nombre: string
  /** Pesos de diferencia contra lo que se hizo de verdad */
  diferencia: number
  /** La misma diferencia en puntos porcentuales sobre el costo */
  diferencia_pct: number | null
}

// Fila del listado: liviana, sin los escenarios (se piden al elegir la venta)
export interface VentaCerrada {
  id: number
  ticker: string
  fecha: string
  cantidad: number
  desde: string
  pnl: number
  pnl_pct: number | null
}

export interface EscenariosDeVenta {
  id: number
  ticker: string
  cantidad: number
  /** Rango en que se puede mover la salida: de la compra a la última rueda */
  desde: string
  hasta: string | null
  real: ResultadoVenta
  escenarios: Escenario[]
  mejor: Escenario | null
}

export interface WhatIf {
  id: number
  ticker: string
  cantidad: number
  real: ResultadoVenta
  alternativo: ResultadoVenta
  diferencia: number
  diferencia_pct: number | null
}

export interface CapturaDeOperacion {
  id: number
  ticker: string
  fecha: string
  costo_unitario: number
  precio_venta: number
  maximo: number
  maximo_fecha: string
  captura_pct: number
}

export interface Captura {
  operaciones: CapturaDeOperacion[]
  promedio_pct: number | null
  medidas: number
}

// Estructura del boleto: arancel + derechos de mercado, con IVA sobre ambos
export interface Comisiones {
  arancel_pct: number
  arancel_intradia_pct: number
  derechos_mercado_pct: number
  iva_pct: number
}

export interface TasaVigente extends Comisiones {
  es_intradia: boolean
  arancel_aplicado_pct: number
  tasa_efectiva_pct: number
}

// --- Optimizador ---

export type MetricaOptimizacion = 'retorno_pct' | 'sharpe' | 'profit_factor' | 'expectancy_pct'

export interface ParametroOptimizacion {
  tipo: 'condicion' | 'riesgo'
  campo: string
  desde: number
  hasta: number
  paso: number
  bloque?: 'entrada' | 'salida' | 'filtros'
  indice?: number
}

export interface ResultadoCombinacion {
  valores: number[]
  metrica: number | null
  retorno_pct: number
  trades: number
  drawdown_pct: number
  buy_and_hold_pct: number
}

export interface AvisoSobreajuste {
  hay_sobreajuste: boolean
  avisos: string[]
}

export interface ResultadoOptimizacion {
  parametros: ParametroOptimizacion[]
  metrica: MetricaOptimizacion
  corte_walk_forward: number | null
  resultados: ResultadoCombinacion[]
  mejor: ResultadoCombinacion | null
  validacion: ResultadoCombinacion | null
  sobreajuste: AvisoSobreajuste
}

export interface EstadoOptimizacion {
  en_curso: boolean
  bot_id: number | null
  hechos: number
  total: number
  resultado: ResultadoOptimizacion | null
  error: string | null
}

export interface BacktestRapidoPeticion {
  ticker: string
  temporalidad: TemporalidadBot
  moneda: Moneda
  capital?: CapitalBot
  riesgo?: RiesgoBot
  reglas: ReglasBot
  meses?: number
}

export type OperadorRegla =
  | 'mayor'
  | 'menor'
  | 'cruza_arriba'
  | 'cruza_abajo'
  | 'cruza_arriba_precio'
  | 'cruza_abajo_precio'

// Objetivo de una condición: constante, otra serie del mismo indicador, o nada
// (en los operadores *_precio, donde el cierre es quien cruza la serie)
export interface ObjetivoSerie {
  serie: string
  params?: Record<string, number>
}

export interface CondicionRegla {
  indicador: string
  serie: string
  operador: OperadorRegla
  objetivo?: number | ObjetivoSerie | null
  params?: Record<string, number>
  // Confluencia: la condición puede mirar una temporalidad superior a la del
  // bot (z mensual en un bot diario). Ausente = la del bot.
  temporalidad?: TemporalidadBot
}

export interface ReglasBot {
  version: number
  entrada: CondicionRegla[]
  salida: CondicionRegla[]
  filtros: CondicionRegla[]
}

export interface RespuestaPreview {
  ts_entrada: number[]
  ts_salida: number[]
}

// Estrategias precargables: las 4 de la metodología (predefinidas) + las que
// guarda el usuario (propias, con id para poder borrarlas)
export interface Plantilla {
  clave: string
  id: number | null
  nombre: string
  descripcion: string
  horizonte: string
  temporalidad: TemporalidadBot
  moneda: Moneda
  reglas: ReglasBot
  predefinida: boolean
}

export interface PlantillaNueva {
  nombre: string
  descripcion: string
  temporalidad: TemporalidadBot
  moneda: Moneda
  reglas: ReglasBot
}

export interface Bot {
  id: number
  nombre: string
  ticker: string
  temporalidad: TemporalidadBot
  moneda: Moneda
  capital: CapitalBot
  riesgo: RiesgoBot
  reglas: ReglasBot
  activo: boolean
  creado: string
  actualizado: string
  metricas: ResumenMetricas | null
}

export interface BotNuevo {
  nombre: string
  ticker: string
  temporalidad: TemporalidadBot
  moneda: Moneda
  capital: CapitalBot
  riesgo?: RiesgoBot
  reglas?: ReglasBot
}

// --- Señales del día ---

// Cada condición de entrada con su valor en la barra del disparo (el "porqué")
export interface CondicionDetalle {
  indicador: string
  serie: string
  temporalidad: TemporalidadBot
  operador: OperadorRegla
  params?: Record<string, number> | null
  valor: number | null
  objetivo: number | null
  objetivo_serie: string | null
  cumple: boolean
}

export interface DetalleSenal {
  bot?: string
  temporalidad?: TemporalidadBot
  moneda?: Moneda
  cierre?: number
  condiciones?: CondicionDetalle[]
}

export interface Senal {
  id: number
  bot_id: number
  ticker: string
  ts_barra: number
  lado: string
  detalle: DetalleSenal
  vista: boolean
  creado: string
  vigente: boolean | null // true sigue cumpliéndose, false ya no, null no evaluable
}

export interface RespuestaSenales {
  senales: Senal[]
  sin_ver: number
}

// --- Análisis transversal (v8) ---

export interface ResumenEstacional {
  promedio_pct: number | null
  mediana_pct: number | null
  positivos_pct: number | null
  casos: number
}

export interface Estacionalidad {
  ticker: string
  moneda: Moneda
  /** Qué mide cada celda: "retorno del mes" o "retorno promedio del día" */
  detalle: string
  columnas: string[]
  anios: number[]
  matriz: (number | null)[][]
  totales_anio: (number | null)[]
  resumen: ResumenEstacional[]
}

export type VistaEstacional = 'mes' | 'dia_semana'

export interface MatrizCorrelacion {
  tickers: string[]
  temporalidad: TemporalidadBot
  moneda: Moneda
  /** `null` cuando el par no llegó al mínimo de ruedas en común */
  matriz: (number | null)[][]
  /** Cuántas ruedas comparten cada par: el respaldo de cada número */
  pares: number[][]
  minimo: number
}

export interface PuntoRolling {
  ts: number
  correlacion: number
}

export interface PuntoDispersion {
  ts: number
  a: number
  b: number
}

export interface CorrelacionPar {
  a: string
  b: string
  temporalidad: TemporalidadBot
  moneda: Moneda
  ventana: number
  puntos: PuntoRolling[]
  correlacion_total: number | null
  /** La de la ventana vigente: el último punto de la línea */
  correlacion_ventana: number | null
  pares: number
  dispersion: PuntoDispersion[]
}
