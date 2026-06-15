# Pantalla de gráficos

La sección **Gráfico** (`paginas/PaginaGrafico.tsx`) es la vista principal: un gráfico
estilo TradingView con su watchlist a la derecha.

## Controles de la barra (de izquierda a derecha)

| Control | Componente | Qué hace |
|---|---|---|
| Logo + ticker | `LogoTicker` | Identidad del papel activo |
| Temporalidad | `SelectorTemporalidad` | 1H · 1D · 1S · 1M (la 1H se oculta en tickers de dólar) |
| Tipo | `SelectorTipoGrafico` | Velas · línea · área (íconos SVG) |
| Volumen | `SelectorVolumen` | Muestra/oculta el histograma de volumen |
| EMA | `SelectorEma` | Muestra/oculta la EMA central (línea dorada) |
| σ | `SelectorBandas` | Muestra/oculta las bandas ±1σ/2σ/3σ (líneas azules) |
| Período | `SelectorPeriodo` | Encuadra el rango visible: 1M · 3M · 6M · 1A · Todo |
| Moneda | `InterruptorMoneda` | Toggle ARS/USD + cotización CCL del día |
| Pantalla completa | `BotonPantallaCompleta` | Fullscreen del gráfico |

Sobre el gráfico, abajo a la derecha, flota el botón **LOG** (`SelectorEscala`):
alterna escala logarítmica / lineal.

## Atajos de teclado (`hooks/usarAtajosTeclado.ts`)

| Tecla | Acción |
|---|---|
| `↑` / `↓` | Ticker anterior / siguiente (recorre la watchlist: favoritos y paneles) |
| `1` `2` `3` `4` | Temporalidad H / D / S / M |
| `$` | Toggle ARS/USD |
| `Cmd/Ctrl + K` | Abrir el buscador de tickers (`BuscadorTickers`) |

Los atajos se ignoran mientras se escribe en un input (no pisan el buscador). La
navegación con flechas trackea la **posición** en la lista, no el ticker, así un
favorito que también está en su panel se recorre en ambos lugares sin loop.

## Preferencias persistidas (localStorage)

Al recargar, la app queda como se dejó:

| Preferencia | Dónde se guarda |
|---|---|
| Ticker | `TickerContext` (`mop.ticker`) |
| Moneda | `MonedaContext` (`mop.moneda`) |
| Favoritos | `FavoritosContext` (`mop.favoritos`) |
| Temporalidad, tipo, escala, volumen | `usarEstadoPersistente` (`mop.temporalidad`, `mop.tipo`, `mop.escala`, `mop.volumen`) |
| EMA central, bandas σ | `usarEstadoPersistente` (`mop.ema`, `mop.bandas`) |

## El gráfico (`componentes/grafico/PanelPrecio.tsx`)

- Construido con **lightweight-charts v4** (`autoSize`, sin logo de atribución).
- La serie se **recrea** al cambiar el tipo (velas/línea/área). El volumen es un
  histograma overlay anclado al 18% inferior, verde/rojo según cierre vs apertura.
- **Crosshair**: `LeyendaOHLC` muestra O/H/L/C, variación contra el cierre anterior
  y volumen de la vela bajo el cursor (sin logo ni ticker: ya están en la barra).
- El rango temporal solo se reencuadra al cambiar de ticker/temporalidad — togglear
  moneda o refrescar **no** pierde el zoom.
- Los botones de período comandan el chart vía `forwardRef` + `useImperativeHandle`
  (`verRango`).
- **Cuidado StrictMode (dev):** los `removeSeries` del cleanup van en try/catch
  porque el `chart.remove()` corre antes y ya libera las series.

## EMA central y bandas σ (la metodología sobre el chart)

El indicador principal de la metodología: una EMA central cuyo **período depende
de la temporalidad** (D=200, S=50, M=12, H=200; ver `config.EMA_POR_TEMPORALIDAD`)
y sus bandas ±1σ/2σ/3σ. Dos toggles independientes: **EMA** (la línea dorada) y
**σ** (las 6 bandas azules, más tenues cuanto más lejos de la media).

- **Backend:** `servicios/indicadores/volatilidad.py` (`bandas`). El router
  `/api/indicadores` inyecta el período según la temporalidad. La σ es la
  **distancia RMS del precio a la EMA**: `sqrt(mean((precio − EMA)²))` sobre la
  ventana, medida alrededor de la EMA (cero), **no** `rolling.std()` (que restaría
  el offset de la EMA atrasada y dejaría al precio casi siempre fuera de las
  bandas). Con esta σ el precio cae dentro de ±2σ ~85% del tiempo y ±3σ ~98%.
- El indicador `z_score` usa **la misma σ**, así `z = ±k` coincide exactamente con
  la banda ±kσ (las señales de bots y las bandas hablan el mismo idioma).
- **Frontend:** el hook `usarBandas` pega a `/api/indicadores?incluir=bandas` solo
  cuando algún toggle está activo (una sola llamada alimenta línea y bandas);
  `seriesBandas.ts` crea las series y mapea los `null` del warmup a huecos.
- **Crosshair:** `LeyendaOHLC` muestra, al lado del volumen, el campo `Z:` con a
  cuántos σ está el precio de la EMA central en la vela bajo el cursor (`zEnIndice`),
  coloreado como semáforo de reversión: blanco dentro de ±1σ, amarillo entre 1 y
  2σ, verde si ≤ −2σ (barato) y rojo si ≥ +2σ (caro).

## Datos

El hook `usarVelas(ticker, temporalidad, moneda)` pega a `/api/velas`. La conversión
a USD la hace el backend (ver `docs/dolar.md`). Los tickers de dólar (DOLARCCL/DOLAROF)
existen en D/S/M (la S y M se resamplean de la diaria); no tienen 1H, por eso ese
botón se oculta para ellos.
