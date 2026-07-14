# Bots

La sección **Bots** (`paginas/bots/PaginaBots.tsx`) administra los robots de
trading: cada bot vigila UN ticker en UNA temporalidad con reglas de entrada y
salida. En v4.1 existe el CRUD completo; las reglas llegan en v4.2/v4.3, la
confluencia multitemporal en v4.4, las plantillas en v4.5 y las señales del día
en v4.6.

## Qué define un bot

| Campo | Valores | Notas |
|---|---|---|
| `nombre` | libre, único | choque de nombre → 409 |
| `ticker` | cualquier ticker con datos | excluidos DOLARCCL/DOLAROF |
| `temporalidad` | `D` · `S` · `M` | la horaria queda fuera de los bots por diseño |
| `moneda` | `ARS` · `USD` | en USD las acciones con ADR usan la serie del ADR, igual que el chart |
| `capital` | `{inicial, porcentaje_por_posicion}` | lo usa el backtest (v5) |
| `reglas` | `{version: 1, entrada, salida, filtros}` | esquema fuerte en v4.2 |
| `activo` | true/false | pausado no genera señales |

## Capas

- **Tabla `bots`** en `app/db.py` — JSON de capital y reglas como TEXT.
- **`repositorios/bots.py`** — CRUD + `duplicar` (copia como "X (copia)", numera
  si ya hay copias). Expone capital/reglas ya parseados: el JSON crudo no sale
  del repositorio.
- **`esquemas/bots.py`** — pydantic: temporalidad `Literal["D","S","M"]`,
  capital validado (inicial > 0, porcentaje 1-100), edición parcial con campos
  opcionales.
- **`routers/bots.py`** — `/api/bots` GET/POST, `/api/bots/{id}` GET/PUT/DELETE,
  `/api/bots/{id}/duplicar` POST. Valida el ticker contra `universo_completo`
  menos los tickers de dólar.
- **Frontend** — `hooks/usarBots.ts` (lista + acciones, recarga tras cada
  mutación), `componentes/bots/FormularioBot.tsx` (alta/edición con buscador de
  ticker), confirmación al borrar como en las listas del sidebar.

## Duplicar es de primera clase

La metodología pide variar la salida de un mismo bot y dejar que el backtest
decida (ver `Documentacion/ESTRATEGIAS_BOTS.md`): duplicar un bot copia todas
sus reglas y queda listo para editarle solo la salida.
