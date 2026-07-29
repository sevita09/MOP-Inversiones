"""Operaciones de cartera: CRUD y precio sugerido desde la vela de la fecha."""
from datetime import datetime, timezone

from app.repositorios import transacciones as repo
from app.repositorios.tasas_dolar import guardar_tasas
from app.repositorios.velas import guardar_velas
from app.servicios.cartera.transacciones import precio_sugerido

# Para el repositorio (guarda precio unitario + comisión ya calculada)
OPERACION = {
    "ticker": "GGAL", "tipo": "compra", "fecha": "2026-03-10",
    "cantidad": 100, "precio": 5000, "comision": 250,
}

# Para la API (el usuario carga precio O monto final; la comisión se despeja)
PETICION = {
    "ticker": "GGAL", "tipo": "compra", "fecha": "2026-03-10",
    "cantidad": 100, "precio": 5000,
}


def _ts(fecha: str) -> int:
    return int(datetime.strptime(fecha, "%Y-%m-%d").replace(tzinfo=timezone.utc).timestamp())


def _sembrar_velas(conexion, precios_por_fecha, ticker="GGAL"):
    guardar_velas(
        conexion,
        [
            {"ticker": ticker, "temporalidad": "D", "ts": _ts(fecha), "apertura": precio,
             "maximo": precio, "minimo": precio, "cierre": precio, "volumen": 1000,
             "es_faltante": 0}
            for fecha, precio in precios_por_fecha.items()
        ],
    )


# --- repositorio ---


def test_crear_y_obtener(conexion):
    creada = repo.crear(conexion, **OPERACION)
    assert creada["id"] == 1
    assert creada["ticker"] == "GGAL"
    assert creada["cantidad"] == 100
    assert creada["comision"] == 250
    assert repo.obtener(conexion, creada["id"]) == creada


def test_listar_ordena_mas_nueva_primero(conexion):
    repo.crear(conexion, **{**OPERACION, "fecha": "2026-01-05"})
    repo.crear(conexion, **{**OPERACION, "fecha": "2026-05-20"})
    repo.crear(conexion, **{**OPERACION, "fecha": "2026-03-10"})
    assert [t["fecha"] for t in repo.listar(conexion)] == [
        "2026-05-20", "2026-03-10", "2026-01-05",
    ]


def test_listar_cronologicas_es_el_orden_del_fifo(conexion):
    repo.crear(conexion, **{**OPERACION, "fecha": "2026-05-20"})
    repo.crear(conexion, **{**OPERACION, "fecha": "2026-01-05"})
    assert [t["fecha"] for t in repo.listar_cronologicas(conexion)] == [
        "2026-01-05", "2026-05-20",
    ]


def test_listar_filtra_por_ticker(conexion):
    repo.crear(conexion, **OPERACION)
    repo.crear(conexion, **{**OPERACION, "ticker": "YPFD"})
    assert len(repo.listar(conexion, "GGAL")) == 1
    assert repo.listar(conexion, "GGAL")[0]["ticker"] == "GGAL"


def test_actualizar_campos_sueltos(conexion):
    creada = repo.crear(conexion, **OPERACION)
    editada = repo.actualizar(conexion, creada["id"], {"cantidad": 50, "nota": "parcial"})
    assert editada["cantidad"] == 50
    assert editada["nota"] == "parcial"
    assert editada["precio"] == 5000  # lo no tocado queda igual


def test_actualizar_inexistente_devuelve_none(conexion):
    assert repo.actualizar(conexion, 99, {"cantidad": 1}) is None


def test_eliminar(conexion):
    creada = repo.crear(conexion, **OPERACION)
    assert repo.eliminar(conexion, creada["id"]) is True
    assert repo.eliminar(conexion, creada["id"]) is False


def test_tickers_operados(conexion):
    repo.crear(conexion, **OPERACION)
    repo.crear(conexion, **{**OPERACION, "ticker": "YPFD"})
    repo.crear(conexion, **{**OPERACION, "ticker": "GGAL", "fecha": "2026-04-01"})
    assert repo.tickers_operados(conexion) == ["GGAL", "YPFD"]


# --- precio sugerido ---


def test_precio_sugerido_toma_el_cierre_de_esa_rueda(conexion):
    _sembrar_velas(conexion, {"2026-03-09": 4800, "2026-03-10": 5100, "2026-03-11": 5300})
    assert precio_sugerido(conexion, "GGAL", "2026-03-10") == 5100


def test_precio_sugerido_usa_la_rueda_anterior_si_no_hubo(conexion):
    # 2026-03-14 es sábado: no hay rueda, toma la del viernes
    _sembrar_velas(conexion, {"2026-03-13": 5200})
    assert precio_sugerido(conexion, "GGAL", "2026-03-14") == 5200


def test_precio_sugerido_sin_historia_es_none(conexion):
    _sembrar_velas(conexion, {"2026-03-10": 5100})
    assert precio_sugerido(conexion, "GGAL", "2020-01-01") is None


def test_precio_sugerido_con_fecha_invalida_es_none(conexion):
    assert precio_sugerido(conexion, "GGAL", "10/03/2026") is None


# --- endpoints: cargando por precio unitario ---


def test_crear_por_precio_calcula_la_comision(cliente, conexion):
    _sembrar_velas(conexion, {"2026-03-10": 5100})
    respuesta = cliente.post("/api/cartera/transacciones", json=PETICION)
    assert respuesta.status_code == 201
    creada = respuesta.json()
    assert creada["bruto"] == 500000  # 100 × 5000
    assert creada["comision"] == 1089.00  # (0,1% + 0,08%) × 1,21 de 500000
    assert creada["monto_final"] == 501089.00  # la compra suma los gastos

    assert len(cliente.get("/api/cartera/transacciones").json()) == 1


def test_la_venta_resta_la_comision(cliente):
    creada = cliente.post("/api/cartera/transacciones", json={**PETICION, "tipo": "venta"}).json()
    assert creada["comision"] == 1089.00
    assert creada["monto_final"] == 498911.00  # 500000 − 1089


# --- endpoints: cargando por monto final (el flujo real del usuario) ---


def test_crear_por_monto_final_despeja_el_precio(cliente):
    """Cargo lo que me cobró el broker y el sistema deduce el precio de mercado."""
    peticion = {
        "ticker": "GGAL", "tipo": "compra", "fecha": "2026-03-10",
        "cantidad": 100, "monto_final": 501089,
    }
    creada = cliente.post("/api/cartera/transacciones", json=peticion).json()
    assert creada["monto_final"] == 501089
    assert round(creada["precio"], 2) == 5000  # despejado con la tasa efectiva
    assert creada["comision"] == 1089.00


def test_monto_final_en_una_venta(cliente):
    peticion = {
        "ticker": "GGAL", "tipo": "venta", "fecha": "2026-03-10",
        "cantidad": 100, "monto_final": 498911,
    }
    creada = cliente.post("/api/cartera/transacciones", json=peticion).json()
    assert round(creada["precio"], 2) == 5000
    assert creada["comision"] == 1089.00


def test_precio_y_monto_final_juntos_es_422(cliente):
    peticion = {**PETICION, "monto_final": 501089}
    assert cliente.post("/api/cartera/transacciones", json=peticion).status_code == 422


def test_sin_precio_ni_monto_final_es_422(cliente):
    peticion = {k: v for k, v in PETICION.items() if k != "precio"}
    assert cliente.post("/api/cartera/transacciones", json=peticion).status_code == 422


# --- gastos con la estructura real del boleto ---


def test_tasas_por_defecto_son_las_del_boleto(cliente):
    config = cliente.get("/api/cartera/comisiones").json()
    assert config["arancel_pct"] == 0.1
    assert config["arancel_intradia_pct"] == 0.05
    assert config["derechos_mercado_pct"] == 0.08
    assert config["iva_pct"] == 21.0


def test_reproduce_el_boleto_real_del_broker(cliente):
    """Compra de 5.000 papeles a $2.180 (resumen real):
        bruto      10.900.000,00
        arancel        10.900,00   (0,1000%)
        d. mercado      8.720,00   (0,0800%)
        IVA             4.120,20   (21% sobre 19.620,00)
        neto       10.923.740,20
    """
    peticion = {
        "ticker": "GGAL", "tipo": "compra", "fecha": "2025-07-14",
        "cantidad": 5000, "precio": 2180,
    }
    creada = cliente.post("/api/cartera/transacciones", json=peticion).json()
    assert creada["bruto"] == 10_900_000
    assert creada["comision"] == 23_740.20  # arancel + derechos + IVA
    assert creada["monto_final"] == 10_923_740.20


def test_cargando_el_importe_neto_devuelve_el_precio_exacto(cliente):
    """El camino inverso del boleto: pego el neto y sale el precio de mercado."""
    peticion = {
        "ticker": "GGAL", "tipo": "compra", "fecha": "2025-07-14",
        "cantidad": 5000, "monto_final": 10_923_740.20,
    }
    creada = cliente.post("/api/cartera/transacciones", json=peticion).json()
    assert round(creada["precio"], 2) == 2180.00
    assert creada["comision"] == 23_740.20


def test_el_desglose_de_gastos_se_puede_consultar(cliente):
    ctx = cliente.get(
        "/api/cartera/tasa_vigente?ticker=GGAL&fecha=2025-07-14&tipo=compra"
    ).json()
    assert ctx["arancel_aplicado_pct"] == 0.1
    # (0,1 + 0,08) × 1,21 = 0,2178%
    assert ctx["tasa_efectiva_pct"] == 0.2178
    assert ctx["es_intradia"] is False


def test_la_venta_del_mismo_dia_usa_el_arancel_intradia(cliente):
    """Comprar y vender el mismo papel el mismo día: arancel 0,05% en vez de 0,1%."""
    cliente.post("/api/cartera/transacciones", json=PETICION)  # compra
    venta = cliente.post(
        "/api/cartera/transacciones", json={**PETICION, "tipo": "venta"}
    ).json()
    # bruto 500.000: arancel 250 + derechos 400 = 650, IVA 136,50 → 786,50
    assert venta["comision"] == 786.50


def test_otra_fecha_no_es_intradia(cliente):
    cliente.post("/api/cartera/transacciones", json=PETICION)
    venta = cliente.post(
        "/api/cartera/transacciones",
        json={**PETICION, "tipo": "venta", "fecha": "2026-03-11"},
    ).json()
    # arancel 500 + derechos 400 = 900, IVA 189 → 1089
    assert venta["comision"] == 1089.00


def test_endpoint_de_tasa_vigente_avisa_el_intradia(cliente):
    cliente.post("/api/cartera/transacciones", json=PETICION)
    ctx = cliente.get(
        "/api/cartera/tasa_vigente?ticker=GGAL&fecha=2026-03-10&tipo=venta"
    ).json()
    assert ctx["es_intradia"] is True
    assert ctx["arancel_aplicado_pct"] == 0.05


def test_las_tasas_se_pueden_cambiar(cliente):
    """Si el broker cambia condiciones (o cambia el IVA), se ajusta sin tocar código."""
    cliente.put(
        "/api/cartera/comisiones",
        json={
            "arancel_pct": 0.5, "arancel_intradia_pct": 0.25,
            "derechos_mercado_pct": 0.1, "iva_pct": 10,
        },
    )
    creada = cliente.post("/api/cartera/transacciones", json=PETICION).json()
    # bruto 500.000: (0,5% + 0,1%) = 3.000, IVA 10% = 300 → 3.300
    assert creada["comision"] == 3300.00


# --- USD, validaciones y edición ---


def test_monto_final_en_usd_con_el_mep_de_la_fecha(cliente, conexion):
    guardar_tasas(conexion, [{"fecha": "2026-03-10", "tipo": "MEP", "valor": 1000}])
    creada = cliente.post("/api/cartera/transacciones", json=PETICION).json()
    assert creada["monto_final_usd"] == 501.089  # 501.089 / 1000


def test_sin_tasa_el_usd_es_none(cliente):
    creada = cliente.post("/api/cartera/transacciones", json=PETICION).json()
    assert creada["monto_final_usd"] is None


def test_ticker_desconocido_es_422(cliente):
    assert cliente.post("/api/cartera/transacciones", json={**PETICION, "ticker": "NADA"}).status_code == 422


def test_fecha_invalida_es_422(cliente):
    assert cliente.post("/api/cartera/transacciones", json={**PETICION, "fecha": "10-03-2026"}).status_code == 422


def test_cantidad_o_precio_no_positivos_son_422(cliente):
    assert cliente.post("/api/cartera/transacciones", json={**PETICION, "cantidad": 0}).status_code == 422
    assert cliente.post("/api/cartera/transacciones", json={**PETICION, "precio": -1}).status_code == 422


def test_editar_la_cantidad_recalcula_la_comision(cliente):
    creada = cliente.post("/api/cartera/transacciones", json=PETICION).json()
    editada = cliente.put(
        f"/api/cartera/transacciones/{creada['id']}", json={"cantidad": 60}
    ).json()
    assert editada["cantidad"] == 60
    assert editada["precio"] == 5000  # se conserva
    assert editada["bruto"] == 300000
    assert editada["comision"] == 653.40  # (0,1% + 0,08%) × 1,21 sobre el bruto nuevo


def test_editar_por_monto_final(cliente):
    creada = cliente.post("/api/cartera/transacciones", json=PETICION).json()
    editada = cliente.put(
        f"/api/cartera/transacciones/{creada['id']}", json={"monto_final": 601200}
    ).json()
    assert editada["monto_final"] == 601200
    assert round(editada["precio"], 2) == 5998.93  # despejado con la tasa efectiva


def test_borrar_por_api(cliente):
    creada = cliente.post("/api/cartera/transacciones", json=PETICION).json()
    assert cliente.delete(f"/api/cartera/transacciones/{creada['id']}").status_code == 200
    assert cliente.delete(f"/api/cartera/transacciones/{creada['id']}").status_code == 404


def test_endpoint_de_precio_sugerido(cliente, conexion):
    _sembrar_velas(conexion, {"2026-03-10": 5100})
    respuesta = cliente.get("/api/cartera/precio_sugerido?ticker=GGAL&fecha=2026-03-10")
    assert respuesta.status_code == 200
    assert respuesta.json()["precio"] == 5100


# --- papeles disponibles para vender ---


def test_cantidades_en_cartera_resta_las_ventas(conexion):
    # Vive en servicios/cartera/posiciones: tiene que aplicar splits, no es una suma SQL
    from app.servicios.cartera.posiciones import cantidades_en_cartera

    repo.crear(conexion, **{**OPERACION, "cantidad": 100})
    repo.crear(conexion, **{**OPERACION, "cantidad": 40, "tipo": "venta"})
    repo.crear(conexion, **{**OPERACION, "ticker": "YPFD", "cantidad": 50})
    assert cantidades_en_cartera(conexion) == {"GGAL": 60, "YPFD": 50}


def test_los_papeles_vendidos_del_todo_no_figuran(conexion):
    from app.servicios.cartera.posiciones import cantidades_en_cartera

    repo.crear(conexion, **{**OPERACION, "cantidad": 100})
    repo.crear(conexion, **{**OPERACION, "cantidad": 100, "tipo": "venta"})
    assert cantidades_en_cartera(conexion) == {}


def test_endpoint_de_papeles_en_cartera(cliente):
    cliente.post("/api/cartera/transacciones", json={**PETICION, "cantidad": 100})
    cliente.post(
        "/api/cartera/transacciones",
        json={**PETICION, "cantidad": 30, "tipo": "venta", "fecha": "2026-04-01"},
    )
    assert cliente.get("/api/cartera/en_cartera").json() == {"GGAL": 70}
