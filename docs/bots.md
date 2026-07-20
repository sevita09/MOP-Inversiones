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

## Reglas (v4.2)

`reglas_json` versionado (`"version": 1`) con tres bloques — `entrada`, `salida`,
`filtros` — de condiciones que se combinan con **AND** (los filtros van AND con
la entrada). Cada condición referencia una serie de un indicador del registry:

```json
{"indicador": "bandas", "serie": "z", "operador": "menor", "objetivo": -2}
{"indicador": "estocastico", "serie": "k", "operador": "cruza_arriba", "objetivo": {"serie": "d"}}
{"indicador": "bandas", "serie": "media", "operador": "cruza_abajo_precio"}
```

- **Operadores**: `mayor`, `menor`, `cruza_arriba`, `cruza_abajo` (objetivo:
  constante u otra serie del mismo indicador) y `cruza_arriba_precio` /
  `cruza_abajo_precio` (el cierre cruza la serie; sin objetivo).
- **`params`** ajusta el indicador (`{"periodo": 20}`); en `objetivo.params`
  permite cruzar dos variantes (EMA rápida × EMA lenta).
- El esquema vive en `esquemas/reglas.py` (`SERIES_POR_INDICADOR` dice qué serie
  tiene cada indicador; un test lo verifica contra el registry real).
- `bandas` expone también la serie **`z`** con la misma σ de las bandas: z = −2
  es exactamente la banda −2σ que muestra el chart.

## Evaluador y vista previa

`servicios/bots/evaluador.py` — **el bot ve lo mismo que el chart**: velas de
`velas_para_vista` (moneda/ADR resueltos) + indicadores de `calcular()`, sin
recalcular nada propio. El período de `bandas`/`percentil_distancia` es la EMA
central de la temporalidad (D=200, S=50, M=12), como en `/api/indicadores`. El
warmup (`None`) nunca cumple una condición, y los cruces piden la barra
anterior completa. Hasta v4.4 todas las condiciones se evalúan en la
temporalidad del bot.

`POST /api/bots/preview` con `{ticker, temporalidad, moneda, reglas}` →
`{ts_entrada: [...], ts_salida: [...]}`: los ts de las barras donde las reglas
hubieran disparado sobre la historia. Es lo que el editor de reglas (v4.3)
pinta como ▲/▼ sobre el gráfico.

## Confluencia multitemporal (v4.4)

Cada condición puede llevar su propia `temporalidad` (igual o **superior** a la
del bot): la Triple Confluencia ejecuta en D con condiciones que miran M y S.

```json
{"indicador": "bandas", "serie": "z", "temporalidad": "M", "operador": "menor", "objetivo": -2}
```

- **Cada temporalidad usa su EMA central** (D=200, S=50, M=12): el z mensual se
  calcula sobre las velas mensuales con EMA 12, igual que el chart en M.
- **La vela superior solo cuenta cerrada** (`servicios/bots/alineacion.py`): el
  sync escribe la vela S/M *en curso* en la base, y usarla sería mirar el
  futuro. Cada barra base ve la última barra superior cuyo período terminó
  **antes** del período en que vive la barra base: el viernes de la semana N ve
  la semana N−1; recién el lunes siguiente ve la semana N. Garantía testeada:
  agregar una barra en curso no cambia ninguna señal pasada.
- Los períodos se comparan por clave de calendario (semana ISO / año-mes), así
  el cruce de año no rompe el orden.
- Una condición de temporalidad **menor** a la del bot es inválida (422).
- En los cruces contra el precio, el precio es el cierre de la temporalidad
  del bot (el TF de ejecución).

## Constructor visual y vista previa (v4.3)

El formulario del bot es un modal de dos columnas: los datos a la izquierda y
las reglas + vista previa a la derecha.

- **`configReglas.ts`** — espejo en el frontend de `SERIES_POR_INDICADOR`, con
  las etiquetas en castellano de indicadores, series y operadores.
- **`FilaCondicion.tsx`** — una condición como fila de selects: indicador →
  serie → operador → objetivo (un valor, otra serie, o nada si el operador es
  "el precio la cruza").
- **`ConstructorReglas.tsx`** — los bloques Entrada/Salida/Filtros con sus
  filas; agregar/quitar condición. El bloque de filtros solo aparece si tiene
  contenido.
- **`GraficoPreviewBot.tsx`** — chart compacto (lightweight-charts) con las
  velas del ticker del bot y las señales de la vista previa como marcadores:
  ▲ verde bajo la barra de entrada, ▼ rojo sobre la barra de salida.
- **`usarPreviewBot.ts`** — llama a `POST /api/bots/preview` con debounce de
  500 ms: editar una condición re-dibuja las señales solo, medio segundo
  después de la última tecla. Una regla inválida a medio editar ⇒ sin señales.

## Duplicar es de primera clase

La metodología pide variar la salida de un mismo bot y dejar que el backtest
decida (ver `Documentacion/ESTRATEGIAS_BOTS.md`): duplicar un bot copia todas
sus reglas y queda listo para editarle solo la salida.
