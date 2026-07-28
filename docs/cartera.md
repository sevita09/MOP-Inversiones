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
calcula con la tasa CCL de esa fecha (`obtener_tasa_en_fecha`).

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
- **P&L no realizado** contra el último cierre conocido, en ARS y en USD (CCL de
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

## Marcas de la cartera en el gráfico

Botón **PPC** en la barra del gráfico (`SelectorTenencia`). Con
`GET /api/cartera/lotes?ticker=&moneda=` trae las compras abiertas y dibuja
(`primitivaTenencia.ts`):

- una **vertical punteada** el día de cada compra, con los papeles que quedan de
  ella tras el FIFO;
- una **horizontal punteada** desde ese día hacia adelante, al precio pagado;
- una **línea llena con el PPC** (promedio ponderado) a lo ancho del gráfico.

**En USD cada compra se convierte con el CCL de su propia fecha**: son los
dólares que se pusieron en ese momento, lo único comparable contra la serie de
precios en dólares. Pasar el promedio en pesos por el CCL de hoy daría un número
que nunca existió (hay un test que fija esa diferencia). Colores y tipo de línea
se editan desde la pestaña **PPC** de la tuerca.
