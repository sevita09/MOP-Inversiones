"""P&L realizado: el resultado de lo que ya se vendió, por FIFO."""
from app.repositorios import splits as repo_splits
from app.repositorios import transacciones as repo
from app.repositorios.tasas_dolar import guardar_tasas
from app.servicios.cartera.posiciones import posicion_de
from app.servicios.cartera.rendimiento import realizado, realizado_de


def _operacion(conexion, tipo, cantidad, precio, fecha, ticker="GGAL", comision=0):
    return repo.crear(conexion, ticker, tipo, fecha, cantidad, precio, comision)


def _mep(conexion, *pares):
    guardar_tasas(
        conexion,
        [{"fecha": fecha, "tipo": "MEP", "valor": valor} for fecha, valor in pares],
    )


def test_sin_ventas_no_hay_realizado(conexion):
    """Una compra sin vender es P&L no realizado, no entra acá."""
    _operacion(conexion, "compra", 100, 1000, "2026-01-10")
    assert realizado_de(conexion, "GGAL") is None


def test_venta_completa(conexion):
    _operacion(conexion, "compra", 100, 1000, "2026-01-10")
    _operacion(conexion, "venta", 100, 1500, "2026-04-01")

    resultado = realizado_de(conexion, "GGAL")
    assert resultado["costo"] == 100_000
    assert resultado["ingreso"] == 150_000
    assert resultado["pnl"] == 50_000
    assert resultado["pnl_pct"] == 50.0


def test_los_gastos_pesan_de_las_dos_puntas(conexion):
    """Los de la compra suben el costo; los de la venta bajan el ingreso."""
    _operacion(conexion, "compra", 100, 1000, "2026-01-10", comision=500)
    _operacion(conexion, "venta", 100, 1500, "2026-04-01", comision=700)

    resultado = realizado_de(conexion, "GGAL")
    assert resultado["costo"] == 100_500
    assert resultado["ingreso"] == 149_300
    assert resultado["pnl"] == 48_800


def test_venta_parcial_toma_el_costo_de_la_compra_mas_vieja(conexion):
    """Vender 60 de 100+100 se lleva el costo de enero, no un promedio."""
    _operacion(conexion, "compra", 100, 1000, "2026-01-10")
    _operacion(conexion, "compra", 100, 2000, "2026-03-10")
    _operacion(conexion, "venta", 60, 2500, "2026-04-01")

    resultado = realizado_de(conexion, "GGAL")
    assert resultado["costo"] == 60_000  # 60 × 1000 (con promedio daría 90.000)
    assert resultado["pnl"] == 90_000  # 60 × (2500 − 1000)
    # Lo que queda sigue siendo no realizado y no se pisa con esto
    assert posicion_de(conexion, "GGAL")["cantidad"] == 140


def test_la_venta_atraviesa_varios_lotes(conexion):
    _operacion(conexion, "compra", 100, 1000, "2026-01-10")
    _operacion(conexion, "compra", 100, 2000, "2026-03-10")
    _operacion(conexion, "venta", 150, 2500, "2026-04-01")

    resultado = realizado_de(conexion, "GGAL")
    assert resultado["costo"] == 200_000  # 100 × 1000 + 50 × 2000
    assert resultado["ingreso"] == 375_000
    assert resultado["pnl"] == 175_000
    assert resultado["ventas"][0]["desde"] == "2026-01-10"


def test_cada_venta_queda_en_el_detalle(conexion):
    _operacion(conexion, "compra", 200, 1000, "2026-01-10")
    _operacion(conexion, "venta", 100, 1500, "2026-04-01")
    _operacion(conexion, "venta", 100, 900, "2026-05-01")

    resultado = realizado_de(conexion, "GGAL")
    assert resultado["operaciones"] == 2
    assert [round(v["pnl"]) for v in resultado["ventas"]] == [50_000, -10_000]
    assert resultado["pnl"] == 40_000


def test_el_split_no_cambia_el_resultado_de_la_venta(conexion):
    """Un 2:1 duplica los papeles y parte el precio: el costo total es el mismo."""
    _operacion(conexion, "compra", 100, 1000, "2026-01-10")
    repo_splits.crear(conexion, "GGAL", "2026-02-01", 2)
    _operacion(conexion, "venta", 200, 600, "2026-04-01")

    resultado = realizado_de(conexion, "GGAL")
    assert resultado["costo"] == 100_000
    assert resultado["ingreso"] == 120_000
    assert resultado["pnl"] == 20_000


def test_en_usd_cada_punta_va_con_el_mep_de_su_fecha(conexion):
    """Se puede ganar en pesos y perder en dólares: el MEP se duplicó."""
    _mep(conexion, ("2026-01-10", 1000), ("2026-04-01", 2000))
    _operacion(conexion, "compra", 100, 1000, "2026-01-10")  # US$100
    _operacion(conexion, "venta", 100, 1500, "2026-04-01")  # US$75

    resultado = realizado_de(conexion, "GGAL")
    assert resultado["pnl"] == 50_000  # en pesos ganó
    assert resultado["pnl_usd"] == -25.0  # en dólares perdió
    assert resultado["ventas"][0]["pnl_usd_pct"] == -25.0


def test_sin_mep_el_resultado_en_usd_es_none(conexion):
    _operacion(conexion, "compra", 100, 1000, "2026-01-10")
    _operacion(conexion, "venta", 100, 1500, "2026-04-01")
    assert realizado_de(conexion, "GGAL")["pnl_usd"] is None


def test_totales_de_la_cartera_por_papel(conexion):
    _mep(conexion, ("2026-01-10", 1000), ("2026-04-01", 1000))
    _operacion(conexion, "compra", 100, 1000, "2026-01-10")
    _operacion(conexion, "venta", 100, 1500, "2026-04-01")
    _operacion(conexion, "compra", 50, 2000, "2026-01-10", ticker="PAMP")
    _operacion(conexion, "venta", 50, 1800, "2026-04-01", ticker="PAMP")

    resultado = realizado(conexion)
    assert [p["ticker"] for p in resultado["papeles"]] == ["GGAL", "PAMP"]  # mejor primero
    assert resultado["totales"]["operaciones"] == 2
    assert resultado["totales"]["costo"] == 200_000
    assert resultado["totales"]["pnl"] == 40_000  # +50.000 y −10.000
    assert resultado["totales"]["pnl_pct"] == 20.0
    assert resultado["totales"]["pnl_usd"] == 40.0
