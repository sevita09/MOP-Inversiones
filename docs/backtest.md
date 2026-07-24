# Backtesting

La etapa v5 simula las reglas de un bot sobre la historia para medir qué habrían
hecho, comparándolas contra Buy & Hold. En v5.1 está el motor; las métricas
(v5.2), la gestión de riesgo (v5.3), la página de resultados (v5.4) y el
optimizador (v5.5) llegan después.

## Principios

- **El backtest ve lo mismo que el chart y los bots**: velas de `velas_para_vista`
  (moneda y ADR resueltos) e indicadores del registry. Las señales salen del
  mismo `evaluar_reglas` que la vista previa y las señales del día.
- **Sin lookahead**: la señal de una barra se conoce recién a su cierre, así que
  la orden se ejecuta en la **apertura de la barra siguiente**, nunca en la misma.
- **Warmup con historia completa**: los indicadores se calculan sobre toda la
  historia para llegar calientes; recién después se recorta la simulación al
  rango pedido (`desde`/`hasta`). Una señal al inicio del rango es válida aunque
  su indicador haya usado datos previos: es warmup, no lookahead.
- **Una posición a la vez** (la metodología es 1 papel por bot).

## Módulos (`servicios/backtest/`)

- **`cargador.py`** — `cargar_historia(conexion, bot)` trae las velas de cada
  temporalidad que usan las reglas (historia completa, para el warmup de la
  confluencia). `recortar(velas, desde, hasta)` deja las barras del rango.
- **`simulador.py`** — `simular(barras, ts_entrada, ts_salida, capital, fraccion)`
  camina barra a barra: ejecuta en la apertura lo que señaló la barra anterior,
  lleva la curva de capital a valor de mercado (al cierre) y arma la lista de
  trades (entrada/salida ts+precio, `pnl_pct`, `duracion_dias`, `gana`,
  `abierto_al_final`). Una posición abierta al final se cierra al cierre de la
  última barra. `fraccion` es la porción del capital por posición
  (`capital.porcentaje_por_posicion / 100`).

## Buy & Hold de comparación

`correr_backtest` corre el mismo simulador dos veces: la **estrategia** (con sus
entradas y salidas) y el **Buy & Hold** (mismas entradas, **sin salidas**, 100%
del capital). Así el B&H entra cuando la estrategia entra pero nunca vende, y la
comparación aísla **cuánto aporta la salida**: "la entrada define si ganás; la
salida, cuánto" (`Documentacion/ESTRATEGIAS_BOTS.md`).

## Endpoint

`GET /api/bots/{id}/backtest?desde=&hasta=` (ts unix, opcionales) →
`{ticker, temporalidad, moneda, desde, hasta, estrategia, buy_and_hold}`, donde
cada lado trae `capital_inicial`, `capital_final`, `retorno_pct`, `trades` y
`curva`. 422 si el bot no tiene reglas de entrada.
