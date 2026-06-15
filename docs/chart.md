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

## Datos

El hook `usarVelas(ticker, temporalidad, moneda)` pega a `/api/velas`. La conversión
a USD la hace el backend (ver `docs/dolar.md`). Los tickers de dólar (DOLARCCL/DOLAROF)
existen en D/S/M (la S y M se resamplean de la diaria); no tienen 1H, por eso ese
botón se oculta para ellos.
