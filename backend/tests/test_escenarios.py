"""What-if: vender antes o después, y cuánto del recorrido se capturó."""
from datetime import datetime, timedelta, timezone

from app.repositorios import transacciones as repo
from app.repositorios.velas import guardar_velas
from app.servicios.cartera.captura import captura_del_recorrido
from app.servicios.cartera.escenarios import (
    escenarios_de,
    pnl_con_fecha,
    tabla_escenarios,
    ventas_cerradas,
)


def _ts(fecha: str) -> int:
    return int(datetime.strptime(fecha, "%Y-%m-%d").replace(tzinfo=timezone.utc).timestamp())


def _serie(conexion, ticker, desde, precios):
    """Una vela diaria por cada precio, arrancando en `desde` (días corridos)."""
    inicio = datetime.strptime(desde, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    guardar_velas(
        conexion,
        [
            {
                "ticker": ticker,
                "temporalidad": "D",
                "ts": int((inicio + timedelta(days=i)).timestamp()),
                "apertura": precio,
                "maximo": precio,
                "minimo": precio,
                "cierre": precio,
                "volumen": 1000,
                "es_faltante": 0,
            }
            for i, precio in enumerate(precios)
        ],
    )


def _operacion(conexion, tipo, cantidad, precio, fecha, ticker="GGAL", comision=0):
    return repo.crear(conexion, ticker, tipo, fecha, cantidad, precio, comision)


def _sin_gastos(conexion):
    """Tasas del broker en cero: deja la aritmética de los escenarios a la vista."""
    from app.repositorios import configuracion as repo_config
    from app.servicios.cartera.comisiones import (
        CLAVE_ARANCEL,
        CLAVE_ARANCEL_INTRADIA,
        CLAVE_DERECHOS,
        CLAVE_IVA,
    )

    for clave in (CLAVE_ARANCEL, CLAVE_ARANCEL_INTRADIA, CLAVE_DERECHOS, CLAVE_IVA):
        repo_config.guardar(conexion, clave, 0)


# Serie conocida: sube de 1000 a 2000 en 10 días y vuelve a 1500
PRECIOS = [1000, 1100, 1200, 1400, 1600, 1800, 2000, 1900, 1700, 1500]
INICIO = "2026-01-01"


def _cartera_de_prueba(conexion):
    """Compra el día 1 a 1000 y vende el día 4 a 1400, con el techo en 2000."""
    _sin_gastos(conexion)
    _serie(conexion, "GGAL", INICIO, PRECIOS)
    _operacion(conexion, "compra", 100, 1000, "2026-01-01")
    return _operacion(conexion, "venta", 100, 1400, "2026-01-04")


# --- P&L con fecha alternativa ---


def test_vender_mas_tarde_en_una_suba_mejora_el_resultado(conexion):
    venta = _cartera_de_prueba(conexion)

    datos = pnl_con_fecha(conexion, venta["id"], "2026-01-07")  # el techo, 2000
    assert datos["real"]["pnl"] == 40_000  # 100 × (1400 − 1000)
    assert datos["alternativo"]["pnl"] == 100_000
    assert datos["diferencia"] == 60_000


def test_vender_mas_temprano_lo_empeora(conexion):
    venta = _cartera_de_prueba(conexion)

    datos = pnl_con_fecha(conexion, venta["id"], "2026-01-02")  # 1100
    assert datos["alternativo"]["pnl"] == 10_000
    assert datos["diferencia"] == -30_000


def test_los_gastos_de_la_venta_alternativa_se_recalculan(conexion):
    """A mayor precio, mayores gastos: no se copian los de la venta real."""
    _serie(conexion, "GGAL", INICIO, PRECIOS)
    _operacion(conexion, "compra", 100, 1000, "2026-01-01")
    venta = _operacion(conexion, "venta", 100, 1400, "2026-01-04", comision=500)

    datos = pnl_con_fecha(conexion, venta["id"], "2026-01-07")
    # Con la tasa efectiva por defecto (0,2178%) sobre 200.000 de bruto
    assert datos["alternativo"]["ingreso"] == round(200_000 - 200_000 * 0.002178, 2)


def test_no_se_puede_vender_antes_de_comprar(conexion):
    venta = _cartera_de_prueba(conexion)
    assert pnl_con_fecha(conexion, venta["id"], "2025-12-15") is None


def test_no_se_puede_vender_despues_de_la_ultima_rueda(conexion):
    venta = _cartera_de_prueba(conexion)
    assert pnl_con_fecha(conexion, venta["id"], "2026-06-01") is None


def test_una_compra_no_tiene_escenarios(conexion):
    _serie(conexion, "GGAL", INICIO, PRECIOS)
    compra = _operacion(conexion, "compra", 100, 1000, "2026-01-01")
    assert pnl_con_fecha(conexion, compra["id"], "2026-01-05") is None
    assert escenarios_de(conexion, compra["id"]) is None


def test_el_split_no_desarma_el_escenario(conexion):
    """Los papeles y el costo salen del FIFO, que ya aplicó el split."""
    from app.repositorios import splits as repo_splits

    _sin_gastos(conexion)
    _serie(conexion, "GGAL", INICIO, PRECIOS)
    _operacion(conexion, "compra", 100, 1000, "2026-01-01")
    repo_splits.crear(conexion, "GGAL", "2026-01-02", 2)
    venta = _operacion(conexion, "venta", 200, 700, "2026-01-04")

    datos = pnl_con_fecha(conexion, venta["id"], "2026-01-05")
    assert datos["cantidad"] == 200
    assert datos["real"]["costo"] == 100_000  # el split no cambia el costo total


# --- tabla de escenarios ---


def test_la_tabla_trae_los_seis_desplazamientos_y_los_dos_extremos(conexion):
    """Con historia suficiente alrededor de la venta entran todos."""
    _sin_gastos(conexion)
    _serie(conexion, "GGAL", "2026-01-01", [1000 + i * 5 for i in range(260)])
    _operacion(conexion, "compra", 100, 1000, "2026-01-15")
    venta = _operacion(conexion, "venta", 100, 1500, "2026-05-01")

    nombres = [e["nombre"] for e in escenarios_de(conexion, venta["id"])["escenarios"]]
    assert nombres == [
        "−3 meses", "−1 mes", "−1 semana", "+1 semana", "+1 mes", "+3 meses",
        "en el máximo", "mantener hasta hoy",
    ]


def test_los_desplazamientos_fuera_de_la_historia_no_entran(conexion):
    """La serie de prueba dura 10 días: ±1 semana cae afuera y se descarta."""
    venta = _cartera_de_prueba(conexion)

    nombres = [e["nombre"] for e in escenarios_de(conexion, venta["id"])["escenarios"]]
    assert nombres == ["en el máximo", "mantener hasta hoy"]


def test_el_maximo_es_el_techo_del_periodo(conexion):
    venta = _cartera_de_prueba(conexion)

    maximo = next(e for e in escenarios_de(conexion, venta["id"])["escenarios"]
                  if e["nombre"] == "en el máximo")
    assert maximo["precio"] == 2000
    assert maximo["fecha"] == "2026-01-07"
    assert maximo["diferencia"] == 60_000


def test_mantener_hasta_hoy_usa_la_ultima_rueda(conexion):
    venta = _cartera_de_prueba(conexion)

    mantener = next(e for e in escenarios_de(conexion, venta["id"])["escenarios"]
                    if e["nombre"] == "mantener hasta hoy")
    assert mantener["precio"] == 1500  # el último de la serie
    assert mantener["diferencia"] == 10_000


def test_cada_escenario_trae_la_diferencia_en_pesos_y_en_puntos(conexion):
    venta = _cartera_de_prueba(conexion)

    maximo = next(e for e in escenarios_de(conexion, venta["id"])["escenarios"]
                  if e["nombre"] == "en el máximo")
    assert maximo["pnl_pct"] == 100.0  # 100.000 sobre 100.000 de costo
    assert maximo["diferencia"] == 60_000
    assert maximo["diferencia_pct"] == 60.0  # 100% contra el 40% real


def test_el_mismo_papel_operado_dos_veces_da_dos_filas(conexion):
    """Compra y vende GGAL, después YPFD, y vuelve a GGAL: son tres ventas.

    Cada una se mide contra las compras que consumió por FIFO, así que la
    segunda vuelta de GGAL no arrastra el costo de la primera.
    """
    _sin_gastos(conexion)
    _serie(conexion, "GGAL", "2026-01-01", [1000 + i * 10 for i in range(200)])
    _serie(conexion, "YPFD", "2026-01-01", [500] * 200)

    _operacion(conexion, "compra", 100, 1000, "2026-01-01")
    _operacion(conexion, "venta", 100, 1300, "2026-01-31")
    _operacion(conexion, "compra", 50, 500, "2026-02-10", ticker="YPFD")
    _operacion(conexion, "venta", 50, 500, "2026-03-10", ticker="YPFD")
    _operacion(conexion, "compra", 100, 2000, "2026-04-11")
    _operacion(conexion, "venta", 100, 2500, "2026-05-11")

    ventas = tabla_escenarios(conexion)["ventas"]
    assert [(v["ticker"], v["real"]["fecha"]) for v in ventas] == [
        ("GGAL", "2026-05-11"),
        ("YPFD", "2026-03-10"),
        ("GGAL", "2026-01-31"),
    ]

    segunda, primera = ventas[0], ventas[2]
    assert primera["real"]["costo"] == 100_000  # la compra de enero a 1000
    assert segunda["real"]["costo"] == 200_000  # la de abril a 2000, no la de enero
    assert primera["desde"] == "2026-01-01"
    assert segunda["desde"] == "2026-04-11"  # el slider arranca en SU compra


def test_el_mejor_escenario_es_el_de_mas_pnl(conexion):
    venta = _cartera_de_prueba(conexion)
    assert escenarios_de(conexion, venta["id"])["mejor"]["nombre"] == "en el máximo"


def test_el_rango_del_slider_va_de_la_compra_a_la_ultima_rueda(conexion):
    venta = _cartera_de_prueba(conexion)
    datos = escenarios_de(conexion, venta["id"])
    assert datos["desde"] == "2026-01-01"
    assert datos["hasta"] == "2026-01-10"


def test_la_tabla_lista_todas_las_ventas(conexion):
    _sin_gastos(conexion)
    _serie(conexion, "GGAL", INICIO, PRECIOS)
    _serie(conexion, "PAMP", INICIO, PRECIOS)
    _operacion(conexion, "compra", 100, 1000, "2026-01-01")
    _operacion(conexion, "venta", 100, 1400, "2026-01-04")
    _operacion(conexion, "compra", 50, 1000, "2026-01-01", ticker="PAMP")
    _operacion(conexion, "venta", 50, 1600, "2026-01-05", ticker="PAMP")

    ventas = tabla_escenarios(conexion)["ventas"]
    assert len(ventas) == 2
    assert ventas[0]["real"]["fecha"] == "2026-01-05"  # la más nueva primero


# --- captura del recorrido ---


def test_la_captura_mide_cuanto_del_techo_se_llevo(conexion):
    """Compró a 1000, el techo mientras la tuvo fue 1400 y vendió justo ahí."""
    venta = _cartera_de_prueba(conexion)

    datos = captura_del_recorrido(conexion)
    operacion = datos["operaciones"][0]
    assert operacion["maximo"] == 1400  # el máximo HASTA la venta, no el de después
    assert operacion["captura_pct"] == 100.0
    assert datos["promedio_pct"] == 100.0
    assert venta["id"] == operacion["id"]


def test_salir_a_mitad_de_camino_captura_la_mitad(conexion):
    _sin_gastos(conexion)
    _serie(conexion, "GGAL", INICIO, PRECIOS)
    _operacion(conexion, "compra", 100, 1000, "2026-01-01")
    # Techo de 1600 el día 5; vende el día 6 a 1300 (la mitad del recorrido)
    _operacion(conexion, "venta", 100, 1300, "2026-01-06")

    operacion = captura_del_recorrido(conexion)["operaciones"][0]
    assert operacion["maximo"] == 1800
    assert operacion["captura_pct"] == round(300 / 800 * 100, 2)


def test_sin_recorrido_no_hay_captura(conexion):
    """Si el papel nunca superó el costo, el porcentaje no significa nada."""
    _serie(conexion, "GGAL", INICIO, [1000, 950, 900, 850])
    _operacion(conexion, "compra", 100, 1000, "2026-01-01")
    _operacion(conexion, "venta", 100, 900, "2026-01-03")

    datos = captura_del_recorrido(conexion)
    assert datos["operaciones"] == []
    assert datos["promedio_pct"] is None


def test_la_captura_toma_el_costo_con_gastos(conexion):
    """Los gastos de la compra suben el costo y bajan el recorrido disponible."""
    _serie(conexion, "GGAL", INICIO, PRECIOS)
    _operacion(conexion, "compra", 100, 1000, "2026-01-01", comision=10_000)  # 1100 por papel
    _operacion(conexion, "venta", 100, 1400, "2026-01-04")

    operacion = captura_del_recorrido(conexion)["operaciones"][0]
    assert operacion["costo_unitario"] == 1100
    assert operacion["captura_pct"] == 100.0  # vendió en el techo de su tenencia


# --- endpoints ---


def test_endpoints_de_whatif(cliente, conexion):
    venta = _cartera_de_prueba(conexion)

    datos = cliente.get(f"/api/cartera/whatif?id_venta={venta['id']}&fecha=2026-01-07").json()
    assert datos["diferencia"] == 60_000
    assert cliente.get(
        f"/api/cartera/whatif?id_venta={venta['id']}&fecha=07-01-2026"
    ).status_code == 422
    assert cliente.get(
        f"/api/cartera/whatif?id_venta={venta['id']}&fecha=2027-01-01"
    ).status_code == 404

    assert cliente.get(f"/api/cartera/escenarios/{venta['id']}").json()["ticker"] == "GGAL"
    assert cliente.get("/api/cartera/escenarios/9999").status_code == 404
    assert len(cliente.get("/api/cartera/escenarios").json()["ventas"]) == 1
    assert cliente.get("/api/cartera/captura").json()["promedio_pct"] == 100.0


def test_el_listado_liviano_no_calcula_escenarios(conexion):
    """Es lo que pide la pantalla: una fila por venta, sin los ocho escenarios."""
    _cartera_de_prueba(conexion)

    ventas = ventas_cerradas(conexion)["ventas"]
    assert len(ventas) == 1
    assert ventas[0]["pnl"] == 40_000
    assert ventas[0]["pnl_pct"] == 40.0
    assert ventas[0]["desde"] == "2026-01-01"
    assert "escenarios" not in ventas[0]


def test_endpoint_de_ventas_cerradas(cliente, conexion):
    _cartera_de_prueba(conexion)
    datos = cliente.get("/api/cartera/ventas_cerradas").json()
    assert [v["ticker"] for v in datos["ventas"]] == ["GGAL"]
