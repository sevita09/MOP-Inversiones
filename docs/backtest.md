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

## Métricas (v5.2)

`servicios/backtest/metricas.py` calcula sobre el resultado de la simulación (no
recalcula nada). Cada lado (estrategia y B&H) trae un dict `metricas`:

- **retorno_pct**, **trades_total**, **trades_ganados**, **win_rate_pct**
- **drawdown_maximo_pct** — peor caída pico-a-valle de la curva de capital
- **sharpe** / **sortino** — sobre los retornos periódicos de la curva,
  anualizados por temporalidad (`BARRAS_POR_ANIO`: D=252, S=52, M=12); el
  Sortino castiga solo la volatilidad a la baja
- **profit_factor** — ganancia bruta / pérdida bruta (en % por trade)
- **expectancy_pct** — resultado promedio por trade
- **exposicion_pct** — % de barras con posición abierta (el simulador cuenta
  `barras_en_posicion`)
- **racha_maxima_perdidas** — máximo de trades perdedores seguidos

Con pocos datos, lo que no tiene sentido devuelve `None` (p.ej. Sharpe de una
curva plana, profit factor sin pérdidas) en vez de un número engañoso.

**Caché en el bot**: tras cada backtest, el endpoint guarda en el bot
(`bots.metricas_json`, vía `repo.guardar_metricas`) un resumen liviano —
`{desde, hasta, estrategia (métricas), buy_and_hold_retorno_pct}`, sin curva ni
trades— para mostrarlo en la lista de bots sin recorrer la historia de nuevo.

## Gestión de riesgo (v5.3)

Cada bot tiene una config de riesgo (`bots.riesgo_json`, esquema `Riesgo`; todo
opcional, sin nada opera como v5.2). El simulador la aplica **intra-barra**
(`servicios/backtest/riesgo.py`):

- **Stop loss** `stop_loss_pct` (% bajo la entrada) y/o **por ATR**
  `stop_atr_mult` (a N ATR bajo la entrada). Con ambos, gana el más protector.
- **Take profit** `take_profit_pct` (% sobre la entrada).
- **Trailing stop** `trailing_pct`: un stop que sube con el máximo y nunca baja.
- **Salida en la EMA central** `salida_ema_central`: vende cuando el cierre
  cruza hacia abajo la EMA central (se suma a las señales de salida, ejecuta en
  la apertura siguiente).
- **Sizing por riesgo** `sizing_riesgo_pct`: dimensiona la posición para perder
  ese % del capital si el precio llega al stop; nunca apalanca. Sin stop, cae a
  la fracción fija del capital.

**Reglas honestas**:
- Stop y take profit se chequean contra el `low`/`high` de la barra. Si ambos
  pudieron tocar en la misma barra, **se asume el stop primero** (peor caso, no
  hay dato del orden intra-barra real).
- Los **gaps** se llenan en la apertura: si la barra abrió más allá del nivel,
  ese es el precio de salida.
- El **ATR** que usan stops y sizing es el de la **barra anterior** (ya cerrada),
  no el de la barra en curso: sin lookahead. El trailing usa el máximo hasta la
  barra previa, así el propio máximo de una barra no sube un stop que su mínimo
  gatilla en la misma barra.

Cada trade guarda su **`motivo`**: `senal` · `stop` · `trailing` · `take_profit`
· `fin`. El trailing se distingue del stop inicial (`stop_es_trailing()`
compara el stop vigente contra el nivel del trailing), así en los resultados se
ve qué parte de la gestión de riesgo actuó en cada cierre.

## Página de resultados (v5.4)

`paginas/backtest/PaginaBacktest.tsx` en la ruta **`/bots/:id/backtest`**, a la
que se llega con el botón 📊 de cada fila en la lista de bots. Corre el backtest
al abrir y lo re-corre al cambiar la ventana (1A · 3A · 5A · Todo,
`usarBacktest`). Muestra:

- **`PanelMetricas`** — el retorno de la estrategia en grande contra el del
  Buy & Hold, con un veredicto ("le gana" / "no le gana") y la grilla de las
  demás métricas, cada una con su explicación al pasar el mouse.
- **`CurvaCapital`** — la curva de capital de la estrategia (verde, sólida) y la
  del Buy & Hold (gris, punteada) sobre el mismo eje: arrancan del mismo capital
  inicial, así la comparación es directa.
- **`GraficoTrades`** — las velas del ticker con cada operación marcada:
  ▲ verde la compra, ▼ la venta coloreada **según el motivo** (rojo stop, verde
  take profit, azul señal, ámbar posición abierta al final) y el resultado en %.
- **`TablaTrades`** — una fila por operación: fechas, precios, duración, motivo
  de salida (con la palabra completa y coloreado: *Stop loss*, *Trailing stop*,
  *Take profit*, *Señal de salida*, *Abierta al final*), resultado y el
  **acumulado compuesto** — cada operación reinvierte sobre lo anterior, así la
  última fila coincide con el retorno de la estrategia (sumar los % daría un
  número inflado que no cierra con la curva).

Los dos gráficos comparten un `sincronizadorTiempo` (el mismo del chart
principal): mover o hacer zoom en uno mueve el otro. Para que los índices
coincidan, el gráfico de precios muestra solo las barras del rango del backtest.

En la **lista de bots**, cada fila muestra el resultado del último backtest
(el resumen cacheado de v5.2) contra el Buy & Hold, sin recalcular nada.

## Backtest rápido desde el editor

`componentes/bots/BacktestRapido.tsx` — botón "⏱ Probar sobre el último año" en
el editor de bots: manda la config **sin guardar** a
`POST /api/bots/backtest_rapido` (`{ticker, temporalidad, moneda, capital,
riesgo, reglas, meses}`) y muestra un resumen en línea (retorno, B&H,
operaciones, aciertos, drawdown). Sirve para iterar reglas sin salir del
formulario ni crear un bot.

## Endpoint

`GET /api/bots/{id}/backtest?desde=&hasta=` (ts unix, opcionales) →
`{ticker, temporalidad, moneda, desde, hasta, estrategia, buy_and_hold}`, donde
cada lado trae `capital_inicial`, `capital_final`, `retorno_pct`, `barras`,
`barras_en_posicion`, `metricas`, `trades` y `curva`. 422 si el bot no tiene
reglas de entrada.
