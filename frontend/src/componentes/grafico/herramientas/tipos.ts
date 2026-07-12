export type TipoHerramienta = 'horizontal' | 'tendencia' | 'fibonacci' | 'medicion' | null

// Punto imantado al centro de una vela (tendencia, fibonacci): usa el ts de la vela.
export interface PuntoDibujo {
  ts: number
  precio: number
}

// Punto de la regla de medición: ancla en coordenada lógica fraccional (libre, no
// imantada a una vela). `ts` se mantiene solo para leer mediciones viejas.
export interface PuntoMedicion {
  logical?: number
  ts?: number
  precio: number
}
