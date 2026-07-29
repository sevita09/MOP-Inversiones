# Cartera

La sección **Cartera** (`paginas/cartera/PaginaCartera.tsx`) registra las
operaciones reales: compras y ventas cargadas a mano. En v6.1 está el historial;
las tenencias por FIFO y el P&L llegan en v6.2.

## Qué guarda una operación

| Campo | Notas |
|---|---|
| `ticker` | cualquiera del universo |
| `tipo` | `compra` · `venta` |
| `fecha` | AAAA-MM-DD |
| `cantidad` | papeles |
| `precio` | **ARS por unidad**, precio de mercado (sin gastos) |
| `comision` | gastos totales de la operación, ya calculados |
| `nota` | libre |

El precio va siempre en ARS porque así se opera en BYMA; la vista en USD se
calcula con el **dólar MEP** de esa fecha (`obtener_tasa_en_fecha`).

## Por qué MEP y no CCL

La cartera se valúa con el MEP (`servicios/cartera/__init__.py`, `TIPO_DOLAR`):
es el dólar que se consigue operando las dos puntas en BYMA, sin sacar la plata
del país, y por eso es el que corresponde a una cartera local. El resto de la
app —gráfico, indicadores, precios del sidebar— sigue con CCL.

    MEP = GGAL.BA / GGALD.BA        (misma acción, sin ratio)
    CCL = GGAL.BA × 10 / GGAL(NYSE) (el ADR equivale a 10 acciones)

`GGALD.BA` entra como un ticker más (`config.TICKER_MEP_BASE`), no se muestra en
la UI y **no se convierte a USD** (ya cotiza en dólares), pero **sí comparte el
calendario de ruedas local** (`tickers_de_la_rueda_local`): si quedara en el
grupo del exterior, el reparador le inventaría placeholders en días que acá no
hubo rueda, y esos placeholders taparían las ruedas reales al calcular la tasa.

## Gastos: la estructura real del boleto

Un boleto cobra **tres** conceptos sobre el importe bruto, y el IVA va sobre la
suma de los dos primeros (`servicios/cartera/comisiones.py`):

```
Arancel        0,1000%   ← del broker (0,05% si es compra-venta en el día)
D. Mercado     0,0800%   ← derechos de mercado
IVA           21,0000%   ← sobre (arancel + derechos)
```

Ejemplo real, verificado como test de regresión
(`test_reproduce_el_boleto_real_del_broker`): compra de 5.000 papeles a $2.180

```
bruto        10.900.000,00
arancel          10.900,00
d. mercado        8.720,00
IVA               4.120,20
importe neto 10.923.740,20
```

La **tasa efectiva** es `(arancel + derechos) × (1 + IVA/100)` = 0,2178% con los
valores por defecto. Las cuatro tasas son configurables (tabla `configuracion`,
`GET`/`PUT /api/cartera/comisiones`, panel ⚙ en la página): si el broker cambia
condiciones o cambia el IVA, se ajusta sin tocar código.

**Intradía automático**: si ese mismo día ya hay una operación del sentido
contrario sobre el mismo papel, se aplica el arancel reducido. No hay que
marcarlo — `hay_operacion_opuesta` lo detecta.

## Las dos formas de cargar

El resumen del broker muestra el **importe neto**, no el precio unitario. Por eso
la operación se puede cargar de dos maneras y el backend despeja la otra:

- **Monto del broker** (default): `cantidad` + `monto_final` → despeja el precio
  de mercado y el desglose de gastos (`desde_monto_final`).
- **Precio unitario**: `cantidad` + `precio` → calcula gastos e importe neto
  (`desde_precio`).

El esquema exige **uno de los dos, no ambos** (`TransaccionPeticion`). El
formulario muestra el desglose completo en vivo antes de guardar.

## Ayudas del formulario

- **Precio sugerido**: al elegir ticker y fecha se propone el cierre de esa rueda
  (`precio_sugerido`); si ese día no hubo rueda, el de la última hábil anterior.
  Cambiar la fecha actualiza el precio.
- **En venta, solo lo que se tiene**: el selector ofrece únicamente los papeles
  en cartera (`GET /api/cartera/en_cartera`, compras − ventas por ticker) y
  precarga la cantidad disponible. Avisa (sin bloquear) si se vende de más.

## Capas

- **Tabla `transacciones`** en `app/db.py`, con índice por `(ticker, fecha)`.
- **`repositorios/transacciones.py`** — CRUD, `listar` (más nuevas primero) y
  `listar_cronologicas` (el orden que necesita el FIFO de v6.2), más
  `cantidades_en_cartera`.
- **`servicios/cartera/`** — `transacciones.py` (validación de fecha, precio
  sugerido, conversión a USD) y `comisiones.py` (tasas y desglose).
- **`routers/cartera.py`** — `/api/cartera/transacciones` CRUD,
  `/precio_sugerido`, `/en_cartera`, `/comisiones`, `/tasa_vigente`.
- **Frontend** — `hooks/usarTransacciones.ts`, `componentes/cartera/`
  (`FormularioOperacion`, `ConfigComisiones`).

## Tenencias por FIFO (v6.2)

`servicios/cartera/posiciones.py` reconstruye la posición recorriendo las
operaciones en orden y consumiendo, en cada venta, **las compras más viejas**
(FIFO — el criterio del fisco). Lo que queda sin consumir es la tenencia actual,
y su costo es el de esos papeles concretos, no un promedio de toda la historia.

- **Los gastos entran al costo**: 100 papeles a $1.000 con $500 de gastos cuestan
  $1.005 cada uno. En una venta parcial se prorratean por unidad.
- **P&L no realizado** contra el último cierre conocido, en ARS y en USD (MEP de
  hoy), con el peso de cada papel en la cartera.
- `GET /api/cartera/tenencias` → `{posiciones, totales}`.

## Splits

Un split no mueve plata: multiplica los papeles y divide su precio. Se registran
en la tabla `splits` (`ratio` = papeles nuevos por papel viejo: 3 es un 3:1, 0.1
un inverso 1:10) y entran al recorrido del FIFO como un evento más, en orden
cronológico:

- los lotes **anteriores** se ajustan (cantidad × ratio, precio ÷ ratio, gastos
  ÷ ratio) y los **posteriores** quedan intactos;
- el **costo total nunca cambia**, que es lo que define un split;
- un split del mismo día que una compra se aplica **después** (esa compra se
  hizo al precio viejo).

Por eso `cantidades_en_cartera` vive en `posiciones.py` y no en el repositorio:
una suma SQL de compras menos ventas ignoraría los splits.

Endpoints: `GET`/`POST`/`DELETE /api/cartera/splits`. UI: botón ⇅ en Cartera,
que traduce el ratio a palabras mientras se escribe para no equivocar el sentido.

## Rendimiento (v7.1)

Pestaña **Rendimiento** de la página Cartera. Responde dos preguntas: cuánto
rindió la cartera de verdad y si le ganó al dólar y al mercado.

La vista tiene su propio selector **Pesos / Dólares**, independiente del toggle
global del gráfico: mirar la cartera en pesos o en dólares son dos preguntas
distintas. La tabla de resultado realizado va siempre en dólares.

### P&L realizado — `servicios/cartera/rendimiento.py`

Lo que ya está cobrado: cada venta contra el costo de las compras que consumió
por FIFO. Es independiente del no realizado de `posiciones.py` — un papel puede
tener las dos cosas si se vendió una parte. Los gastos pesan de las dos puntas
(los de la compra están en el costo del lote, los de la venta bajan el ingreso).

**En USD cada punta va con el MEP de su fecha**: los dólares que se pusieron
contra los que se sacaron. Se puede ganar en pesos y perder en dólares, y la
tabla lo muestra.

### Curva de valor y flujos — `servicios/cartera/curva.py`

Rueda por rueda: la tenencia de cada papel (reconstruida desde las operaciones
y los splits) por el cierre de ese día. Aparte, el **flujo** del día: lo que
entró al comprar (precio + gastos) y lo que salió al vender (precio − gastos).

Separar valor de flujo es lo que hace calculable el TWR. En USD todo se
convierte con el MEP de **esa** rueda.

### TWR y benchmarks — `servicios/cartera/benchmarks.py`

El retorno simple engaña apenas hay flujos: meter plata justo antes de una suba
infla el porcentaje sin haber acertado nada. El **TWR** parte la historia en
tramos entre flujo y flujo y los encadena:

```
r_t = (V_t − F_t) / V_(t−1) − 1        TWR = Π (1 + r_t) − 1
```

Los benchmarks van todos a base 100 desde la misma rueda que la cartera:

| Serie | Qué responde |
|---|---|
| Dólar MEP | ¿le gané al dólar con el que me valúo? |
| Dólar CCL | ¿se abrió o cerró la brecha entre los dos dólares? |
| MERVAL | ¿le gané al mercado? |
| Inflación | ¿le gané al costo de vida? (solo en pesos) |

En la vista en dólares las tasas se miden contra el MEP: el MEP queda plano
—quedarse en dólares no rinde en dólares— y el CCL muestra la brecha. La
inflación no aparece en dólares: es un fenómeno en pesos.

La **inflación** es el IPC nacional del INDEC vía `api.argentinadatos.com`
(`servicios/inflacion.py`). La serie es mensual y se encadena en un índice
(`índice *= 1 + variación/100`); dentro del mes no se mueve, porque el dato es
mensual y fabricar un recorrido diario sería precisión inventada. Se consulta
**entre el 11 y el 15 de cada mes, una vez por hora** (el INDEC publica cerca
del 13), salvo la carga inicial. El MERVAL es el índice real de Yahoo (`^MERV`, `config.INDICES_LOCALES`), no un
índice armado a mano: cotiza en pesos, entra al sync como cualquier papel y en
la vista USD se divide por el MEP de cada rueda (el "Merval en dólares").

Endpoints: `GET /api/cartera/realizado` y
`GET /api/cartera/rendimiento?moneda=&desde=`.

## Marcas de la cartera en el gráfico

Dos capas distintas, las dos en `servicios/cartera/marcas.py`:

| | **PPC** (v6.2) | **Operaciones** (v7.2) |
|---|---|---|
| Botón | `PPC` | `Ops` |
| Qué muestra | las compras que siguen abiertas tras el FIFO | todas las órdenes, compras y ventas |
| Posición cerrada | no aparece | aparece completa |
| Precio | con gastos (es el costo) | de mercado (es donde se ejecutó) |
| Pregunta | ¿dónde está mi costo hoy? | ¿cómo operé? |

**Las dos convierten con CCL, no con el MEP** que valúa la cartera: son objetos
que se dibujan sobre la serie del gráfico, y esa serie se convierte con CCL
(`precio_para_vista` en `servicios/dolar.py`). Con MEP quedarían corridas ~4%.

Y en los papeles **con ADR** el gráfico en dólares muestra el certificado, que
vale `ratio` acciones locales: la marca se multiplica por el ratio para caer
sobre esa serie. Verificado: una compra de GGAL a $5.520 el 16/09/24 marca
US$44,33, que es exactamente el cierre del ADR de esa rueda.

Desde **Tenencias**, tocar el nombre del papel abre su gráfico con las
operaciones ya marcadas.

### PPC (v6.2)

Botón **PPC** en la barra del gráfico (`SelectorTenencia`). Con
`GET /api/cartera/lotes?ticker=&moneda=` trae las compras abiertas y dibuja
(`primitivaTenencia.ts`):

- una **vertical punteada** el día de cada compra, con los papeles que quedan de
  ella tras el FIFO;
- una **horizontal punteada** desde ese día hacia adelante, al precio pagado;
- una **línea llena con el PPC** (promedio ponderado) a lo ancho del gráfico.

**En USD cada compra se convierte con el MEP de su propia fecha**: son los
dólares que se pusieron en ese momento, lo único comparable contra la serie de
precios en dólares. Pasar el promedio en pesos por el CCL de hoy daría un número
que nunca existió (hay un test que fija esa diferencia). Colores y tipo de línea
se editan desde la pestaña **PPC** de la tuerca.
