# Manejo del dólar

La plataforma maneja dos tipos de dólar y convierte cualquier papel BYMA a USD.

## Tasa CCL (Contado con Liquidación)

Se calcula a partir de GGAL, que cotiza en dos mercados:

```
CCL = (GGAL en BYMA, ARS) × 10 / (ADR de GGAL en NYSE, USD)
```

El factor 10 es porque cada ADR equivale a 10 acciones locales. La serie se
recalcula tras cada sync desde las velas diarias guardadas (`sincronizar_ccl`),
solo en las fechas con vela real de ambos lados.

## Dólar oficial

Se baja de yfinance (`USDARS=X` → ticker interno `DOLAROF`) y se guarda como
velas y como tasas tipo `OFICIAL`.

## Tickers sintéticos

| Ticker | Origen | Para qué |
|---|---|---|
| `DOLARCCL` | velas generadas desde la serie CCL (OHLC = valor) | graficar el CCL como un papel más |
| `DOLAROF` | yfinance `USDARS=X` | graficar y comparar contra el CCL |

## Conversión ARS → USD

La hace **el backend**, no el frontend:

```
GET /api/velas?ticker=GGAL&temporalidad=D&moneda=USD
```

- Divide cada OHLC por la tasa CCL **de la fecha de esa vela** (búsqueda binaria
  sobre las tasas ordenadas).
- Días sin tasa exacta (feriados, fines de semana) usan la **última tasa
  disponible** (día hábil anterior).
- Velas anteriores a la primera tasa conocida se descartan.
- Solo se convierten los papeles BYMA. AAPL, `DOLARCCL` y `DOLAROF` nunca se
  convierten (ya están en su moneda).
- `moneda` por defecto es `ARS`; valores válidos: `ARS`, `USD`.

## Frontend

`contextos/MonedaContext.tsx` expone `usarMoneda()` con `moneda`, `alternarMoneda`
y `esUSD`. La preferencia se persiste en `localStorage`. El toggle ARS/USD vive
en el header (`InterruptorMoneda`). Los componentes de gráfico leerán `esUSD`
para pedir las velas en la moneda elegida.
