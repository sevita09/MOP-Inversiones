"""Tenencias por FIFO: consumo de lotes, costo con gastos y P&L no realizado."""
from datetime import datetime, timezone

from app.repositorios import transacciones as repo
from app.repositorios.tasas_dolar import guardar_tasas
from app.repositorios.velas import guardar_velas
from app.servicios.cartera.posiciones import posicion_de, tenencias


def _ts(fecha: str) -> int:
    return int(datetime.strptime(fecha, "%Y-%m-%d").replace(tzinfo=timezone.utc).timestamp())


def _precio_de_mercado(conexion, ticker, precio, fecha="2026-06-01"):
    guardar_velas(
        conexion,
        [{"ticker": ticker, "temporalidad": "D", "ts": _ts(fecha), "apertura": precio,
          "maximo": precio, "minimo": precio, "cierre": precio, "volumen": 1000,
          "es_faltante": 0}],
    )


def _operacion(conexion, tipo, cantidad, precio, fecha, ticker="GGAL", comision=0):
    return repo.crear(conexion, ticker, tipo, fecha, cantidad, precio, comision)


# --- FIFO ---


def test_una_compra_es_la_posicion(conexion):
    _operacion(conexion, "compra", 100, 1000, "2026-01-10")
    posicion = posicion_de(conexion, "GGAL")
    assert posicion["cantidad"] == 100
    assert posicion["costo"] == 100_000
    assert posicion["precio_promedio"] == 1000


def test_los_gastos_entran_al_costo(conexion):
    """100 papeles a $1.000 con $500 de gastos cuestan $1.005 cada uno."""
    _operacion(conexion, "compra", 100, 1000, "2026-01-10", comision=500)
    posicion = posicion_de(conexion, "GGAL")
    assert posicion["costo"] == 100_500
    assert posicion["precio_promedio"] == 1005


def test_la_venta_consume_la_compra_mas_vieja(conexion):
    """FIFO: vender 60 se lleva la compra de enero, no la de marzo."""
    _operacion(conexion, "compra", 100, 1000, "2026-01-10")
    _operacion(conexion, "compra", 100, 2000, "2026-03-10")
    _operacion(conexion, "venta", 60, 2500, "2026-04-01")

    posicion = posicion_de(conexion, "GGAL")
    assert posicion["cantidad"] == 140  # 40 de enero + 100 de marzo
    # 40 × 1000 + 100 × 2000 = 240.000 (si fuera promedio daría 210.000)
    assert posicion["costo"] == 240_000


def test_la_venta_atraviesa_varios_lotes(conexion):
    _operacion(conexion, "compra", 100, 1000, "2026-01-10")
    _operacion(conexion, "compra", 100, 2000, "2026-03-10")
    _operacion(conexion, "venta", 150, 2500, "2026-04-01")  # se come el lote 1 y medio lote 2

    posicion = posicion_de(conexion, "GGAL")
    assert posicion["cantidad"] == 50
    assert posicion["costo"] == 100_000  # 50 × 2000, todo del segundo lote


def test_vender_todo_deja_la_posicion_cerrada(conexion):
    _operacion(conexion, "compra", 100, 1000, "2026-01-10")
    _operacion(conexion, "venta", 100, 1500, "2026-02-10")
    assert posicion_de(conexion, "GGAL") is None


def test_los_gastos_se_prorratean_en_la_venta_parcial(conexion):
    """De 100 papeles con $1.000 de gastos ($10 c/u), quedan 40 → $400 de gastos."""
    _operacion(conexion, "compra", 100, 1000, "2026-01-10", comision=1000)
    _operacion(conexion, "venta", 60, 1500, "2026-02-10")
    posicion = posicion_de(conexion, "GGAL")
    assert posicion["cantidad"] == 40
    assert posicion["costo"] == 40_400  # 40 × (1000 + 10)


def test_recompra_despues_de_vender_todo(conexion):
    _operacion(conexion, "compra", 100, 1000, "2026-01-10")
    _operacion(conexion, "venta", 100, 1500, "2026-02-10")
    _operacion(conexion, "compra", 50, 3000, "2026-05-10")
    posicion = posicion_de(conexion, "GGAL")
    assert posicion["cantidad"] == 50
    assert posicion["costo"] == 150_000  # solo la compra nueva
    assert posicion["desde"] == "2026-05-10"


# --- P&L no realizado ---


def test_pnl_con_el_ultimo_precio_de_mercado(conexion):
    _operacion(conexion, "compra", 100, 1000, "2026-01-10")
    _precio_de_mercado(conexion, "GGAL", 1500)
    posicion = posicion_de(conexion, "GGAL")
    assert posicion["precio_actual"] == 1500
    assert posicion["valor_actual"] == 150_000
    assert posicion["pnl"] == 50_000
    assert posicion["pnl_pct"] == 50.0


def test_pnl_negativo(conexion):
    _operacion(conexion, "compra", 100, 1000, "2026-01-10")
    _precio_de_mercado(conexion, "GGAL", 800)
    posicion = posicion_de(conexion, "GGAL")
    assert posicion["pnl"] == -20_000
    assert posicion["pnl_pct"] == -20.0


def test_sin_precio_de_mercado_el_pnl_es_none(conexion):
    _operacion(conexion, "compra", 100, 1000, "2026-01-10")
    posicion = posicion_de(conexion, "GGAL")
    assert posicion["valor_actual"] is None
    assert posicion["pnl"] is None
    assert posicion["costo"] == 100_000  # el costo sí se conoce


# --- cartera completa ---


def test_totales_y_peso_por_papel(conexion):
    _operacion(conexion, "compra", 100, 1000, "2026-01-10", ticker="GGAL")
    _operacion(conexion, "compra", 50, 2000, "2026-01-10", ticker="YPFD")
    _precio_de_mercado(conexion, "GGAL", 1500)  # vale 150.000
    _precio_de_mercado(conexion, "YPFD", 1000)  # vale 50.000

    resultado = tenencias(conexion)
    totales = resultado["totales"]
    assert totales["costo"] == 200_000  # 100.000 + 100.000
    assert totales["valor_actual"] == 200_000  # 150.000 + 50.000
    assert totales["pnl"] == 0

    # Ordenadas por valor: GGAL primero (75% de la cartera)
    posiciones = resultado["posiciones"]
    assert [p["ticker"] for p in posiciones] == ["GGAL", "YPFD"]
    assert posiciones[0]["peso_pct"] == 75.0
    assert posiciones[1]["peso_pct"] == 25.0


def test_los_papeles_cerrados_no_figuran(conexion):
    _operacion(conexion, "compra", 100, 1000, "2026-01-10", ticker="GGAL")
    _operacion(conexion, "venta", 100, 1500, "2026-02-10", ticker="GGAL")
    _operacion(conexion, "compra", 50, 2000, "2026-01-10", ticker="YPFD")
    assert [p["ticker"] for p in tenencias(conexion)["posiciones"]] == ["YPFD"]


def test_valores_en_usd_con_el_mep(conexion):
    _operacion(conexion, "compra", 100, 1000, "2026-01-10")
    _precio_de_mercado(conexion, "GGAL", 1500)
    guardar_tasas(conexion, [{"fecha": "2026-06-01", "tipo": "MEP", "valor": 1000}])

    resultado = tenencias(conexion)
    assert resultado["totales"]["tasa_ccl"] == 1000
    assert resultado["totales"]["valor_usd"] == 150.0  # 150.000 / 1000
    assert resultado["totales"]["pnl_usd"] == 50.0
    assert resultado["posiciones"][0]["valor_usd"] == 150.0


def test_sin_tasa_los_valores_en_usd_son_none(conexion):
    _operacion(conexion, "compra", 100, 1000, "2026-01-10")
    _precio_de_mercado(conexion, "GGAL", 1500)
    assert tenencias(conexion)["totales"]["valor_usd"] is None


def test_cartera_vacia(conexion):
    resultado = tenencias(conexion)
    assert resultado["posiciones"] == []
    assert resultado["totales"]["costo"] == 0


# --- endpoint ---


def test_endpoint_de_tenencias(cliente, conexion):
    _operacion(conexion, "compra", 100, 1000, "2026-01-10")
    _precio_de_mercado(conexion, "GGAL", 1200)
    respuesta = cliente.get("/api/cartera/tenencias")
    assert respuesta.status_code == 200
    datos = respuesta.json()
    assert datos["posiciones"][0]["ticker"] == "GGAL"
    assert datos["totales"]["pnl"] == 20_000


# --- splits ---


def _split(conexion, fecha, ratio, ticker="GGAL"):
    from app.repositorios import splits as repo_splits

    return repo_splits.crear(conexion, ticker, fecha, ratio)


def test_split_multiplica_los_papeles_sin_cambiar_el_costo(conexion):
    """Split 3:1 — el mismo dinero repartido en el triple de papeles."""
    _operacion(conexion, "compra", 100, 3000, "2026-01-10")
    _split(conexion, "2026-02-01", 3)

    posicion = posicion_de(conexion, "GGAL")
    assert posicion["cantidad"] == 300
    assert posicion["costo"] == 300_000  # no cambia
    assert posicion["precio_promedio"] == 1000  # 3000 / 3


def test_split_inverso_reduce_los_papeles(conexion):
    """Contrasplit 1:10 — diez veces menos papeles, diez veces más caros."""
    _operacion(conexion, "compra", 1000, 50, "2026-01-10")
    _split(conexion, "2026-02-01", 0.1)

    posicion = posicion_de(conexion, "GGAL")
    assert posicion["cantidad"] == 100
    assert posicion["costo"] == 50_000
    assert posicion["precio_promedio"] == 500


def test_el_split_no_toca_las_compras_posteriores(conexion):
    _operacion(conexion, "compra", 100, 3000, "2026-01-10")  # se triplica
    _split(conexion, "2026-02-01", 3)
    _operacion(conexion, "compra", 50, 1000, "2026-03-10")  # ya post-split

    posicion = posicion_de(conexion, "GGAL")
    assert posicion["cantidad"] == 350  # 300 + 50
    assert posicion["costo"] == 350_000  # 300.000 + 50.000


def test_el_split_del_mismo_dia_se_aplica_despues_de_la_compra(conexion):
    """Comprar el día del split: el precio pagado es el viejo, así que ajusta."""
    _operacion(conexion, "compra", 100, 3000, "2026-02-01")
    _split(conexion, "2026-02-01", 3)
    assert posicion_de(conexion, "GGAL")["cantidad"] == 300


def test_venta_despues_del_split_consume_papeles_ajustados(conexion):
    _operacion(conexion, "compra", 100, 3000, "2026-01-10")
    _split(conexion, "2026-02-01", 3)  # ahora hay 300 a $1.000
    _operacion(conexion, "venta", 120, 1200, "2026-03-01")

    posicion = posicion_de(conexion, "GGAL")
    assert posicion["cantidad"] == 180
    assert posicion["costo"] == 180_000  # 180 × 1000


def test_los_gastos_tambien_se_ajustan_en_el_split(conexion):
    """$1.000 de gastos sobre 100 papeles ($10 c/u) pasan a $3,33 sobre 300."""
    _operacion(conexion, "compra", 100, 3000, "2026-01-10", comision=1000)
    _split(conexion, "2026-02-01", 3)

    posicion = posicion_de(conexion, "GGAL")
    assert posicion["cantidad"] == 300
    assert posicion["costo"] == 301_000  # el costo total no cambia


def test_dos_splits_encadenados(conexion):
    _operacion(conexion, "compra", 100, 6000, "2026-01-10")
    _split(conexion, "2026-02-01", 3)  # 300 a $2.000
    _split(conexion, "2026-05-01", 2)  # 600 a $1.000

    posicion = posicion_de(conexion, "GGAL")
    assert posicion["cantidad"] == 600
    assert posicion["precio_promedio"] == 1000
    assert posicion["costo"] == 600_000


def test_los_papeles_disponibles_consideran_el_split(conexion):
    """Lo que ofrece el formulario de venta tiene que ser la cantidad ajustada."""
    from app.servicios.cartera.posiciones import cantidades_en_cartera

    _operacion(conexion, "compra", 100, 3000, "2026-01-10")
    _split(conexion, "2026-02-01", 3)
    assert cantidades_en_cartera(conexion) == {"GGAL": 300}


def test_endpoints_de_splits(cliente, conexion):
    _operacion(conexion, "compra", 100, 3000, "2026-01-10")
    creado = cliente.post(
        "/api/cartera/splits",
        json={"ticker": "GGAL", "fecha": "2026-02-01", "ratio": 3, "nota": "split 3:1"},
    )
    assert creado.status_code == 201
    assert cliente.get("/api/cartera/tenencias").json()["posiciones"][0]["cantidad"] == 300

    # Repetir el mismo papel y fecha es conflicto
    assert cliente.post(
        "/api/cartera/splits", json={"ticker": "GGAL", "fecha": "2026-02-01", "ratio": 3}
    ).status_code == 409

    # Al borrarlo, la posición vuelve a la cantidad original
    assert cliente.delete(f"/api/cartera/splits/{creado.json()['id']}").status_code == 200
    assert cliente.get("/api/cartera/tenencias").json()["posiciones"][0]["cantidad"] == 100
