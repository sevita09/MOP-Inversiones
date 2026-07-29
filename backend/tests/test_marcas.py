"""Marcas de la cartera sobre el gráfico: PPC (v6.2) y operaciones (v7.2).

Las dos convierten con **CCL**, no con el MEP con que se valúa la cartera: son
objetos que se dibujan encima de la serie del gráfico, y esa serie se convierte
con CCL. Si usaran MEP quedarían corridas varios puntos.
"""
from datetime import datetime, timezone

from app.repositorios import transacciones as repo
from app.repositorios.tasas_dolar import guardar_tasas
from app.repositorios.velas import guardar_velas
from app.servicios.cartera.marcas import lotes_abiertos, operaciones_de


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


def _ccl(conexion, *pares):
    guardar_tasas(
        conexion, [{"fecha": f, "tipo": "CCL", "valor": v} for f, v in pares]
    )


# --- PPC: compras abiertas ---


def test_lotes_abiertos_con_su_ppc(conexion):
    _operacion(conexion, "compra", 100, 1000, "2026-01-10")
    _operacion(conexion, "compra", 100, 2000, "2026-03-10")
    _operacion(conexion, "venta", 50, 2500, "2026-04-01")  # se lleva medio lote 1

    datos = lotes_abiertos(conexion, "GGAL")
    assert [l["cantidad"] for l in datos["lotes"]] == [50, 100]
    assert [l["precio"] for l in datos["lotes"]] == [1000, 2000]
    assert datos["cantidad"] == 150
    # PPC ponderado: (50×1000 + 100×2000) / 150
    assert datos["ppc"] == round(250_000 / 150, 6)


def test_los_lotes_traen_el_ts_de_la_rueda(conexion):
    _precio_de_mercado(conexion, "GGAL", 1000, fecha="2026-01-10")
    _operacion(conexion, "compra", 100, 1000, "2026-01-10")
    assert lotes_abiertos(conexion, "GGAL")["lotes"][0]["ts"] == _ts("2026-01-10")


def test_los_lotes_incluyen_los_gastos_en_el_precio(conexion):
    _operacion(conexion, "compra", 100, 1000, "2026-01-10", comision=500)
    assert lotes_abiertos(conexion, "GGAL")["lotes"][0]["precio"] == 1005


def test_sin_posicion_no_hay_lotes(conexion):
    datos = lotes_abiertos(conexion, "GGAL")
    assert datos["lotes"] == [] and datos["ppc"] is None


def test_endpoint_de_lotes(cliente, conexion):
    _operacion(conexion, "compra", 100, 1000, "2026-01-10")
    datos = cliente.get("/api/cartera/lotes?ticker=GGAL").json()
    assert datos["ticker"] == "GGAL"
    assert datos["ppc"] == 1000


def test_los_lotes_en_usd_usan_el_ccl_de_su_fecha(conexion):
    """Cada compra vale los dólares que costó ESE día, no los de hoy.

    GGAL tiene ADR (ratio 10): en USD el gráfico muestra el certificado, así que
    la marca se multiplica por el ratio para caer sobre esa serie.
    """
    _ccl(conexion, ("2026-01-10", 1000), ("2026-06-10", 1500))
    _operacion(conexion, "compra", 100, 1000, "2026-01-10")  # 1000×10/1000 = US$10
    _operacion(conexion, "compra", 100, 3000, "2026-06-10")  # 3000×10/1500 = US$20

    datos = lotes_abiertos(conexion, "GGAL", "USD")
    assert [l["precio"] for l in datos["lotes"]] == [10, 20]
    assert datos["ppc"] == 15
    # En pesos el promedio es otro: 2000, y pasarlo por un CCL no daría 15
    assert lotes_abiertos(conexion, "GGAL", "ARS")["ppc"] == 2000


def test_un_papel_sin_adr_no_multiplica(conexion):
    """COME no tiene certificado: en USD es la acción dividida por el CCL."""
    _ccl(conexion, ("2026-01-10", 1000))
    _operacion(conexion, "compra", 100, 1000, "2026-01-10", ticker="COME")
    assert lotes_abiertos(conexion, "COME", "USD")["lotes"][0]["precio"] == 1


def test_sin_ccl_de_esa_fecha_el_lote_no_se_ubica(conexion):
    _operacion(conexion, "compra", 100, 1000, "2026-01-10")
    assert lotes_abiertos(conexion, "GGAL", "USD")["lotes"] == []


def test_endpoint_de_lotes_en_usd(cliente, conexion):
    _operacion(conexion, "compra", 100, 1000, "2026-01-10")
    _ccl(conexion, ("2026-01-10", 1000))
    datos = cliente.get("/api/cartera/lotes?ticker=GGAL&moneda=USD").json()
    assert datos["moneda"] == "USD"
    assert datos["ppc"] == 10


# --- operaciones: el historial completo ---


def test_las_operaciones_incluyen_compras_y_ventas(conexion):
    _operacion(conexion, "compra", 100, 1000, "2026-01-10")
    _operacion(conexion, "venta", 100, 1500, "2026-04-01")

    datos = operaciones_de(conexion, "GGAL")
    assert [o["tipo"] for o in datos["operaciones"]] == ["compra", "venta"]
    assert [o["precio"] for o in datos["operaciones"]] == [1000, 1500]


def test_una_posicion_cerrada_sigue_teniendo_operaciones(conexion):
    """Lo que el PPC no muestra: el papel que ya se vendió del todo."""
    _operacion(conexion, "compra", 100, 1000, "2026-01-10")
    _operacion(conexion, "venta", 100, 1500, "2026-04-01")

    assert lotes_abiertos(conexion, "GGAL")["lotes"] == []
    assert len(operaciones_de(conexion, "GGAL")["operaciones"]) == 2


def test_el_precio_de_la_marca_es_el_de_mercado(conexion):
    """Sin gastos: la flecha marca dónde se ejecutó la orden, no cuánto costó."""
    _operacion(conexion, "compra", 100, 1000, "2026-01-10", comision=500)
    assert operaciones_de(conexion, "GGAL")["operaciones"][0]["precio"] == 1000


def test_las_operaciones_traen_el_ts_de_la_rueda(conexion):
    _precio_de_mercado(conexion, "GGAL", 1000, fecha="2026-01-10")
    _operacion(conexion, "compra", 100, 1000, "2026-01-10")
    assert operaciones_de(conexion, "GGAL")["operaciones"][0]["ts"] == _ts("2026-01-10")


def test_las_operaciones_en_usd_usan_el_ccl(conexion):
    _ccl(conexion, ("2026-01-10", 1000))
    _operacion(conexion, "compra", 100, 1000, "2026-01-10")
    assert operaciones_de(conexion, "GGAL", "USD")["operaciones"][0]["precio"] == 10


def test_endpoint_de_operaciones(cliente, conexion):
    _operacion(conexion, "compra", 100, 1000, "2026-01-10")
    _operacion(conexion, "venta", 40, 1500, "2026-04-01")

    datos = cliente.get("/api/cartera/operaciones_grafico?ticker=GGAL").json()
    assert len(datos["operaciones"]) == 2
    assert datos["operaciones"][1]["cantidad"] == 40
    assert cliente.get("/api/cartera/operaciones_grafico?ticker=GGAL&moneda=EUR").status_code == 422
