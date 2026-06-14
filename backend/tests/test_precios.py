from app.repositorios.tasas_dolar import CCL, guardar_tasas
from app.repositorios.velas import guardar_velas
from app.servicios.precios import calcular_precios, precio_de_ticker

UN_DIA = 86400


def vela(ticker, ts, cierre):
    return {
        "ticker": ticker,
        "temporalidad": "D",
        "ts": ts,
        "apertura": cierre,
        "maximo": cierre,
        "minimo": cierre,
        "cierre": cierre,
        "volumen": 100.0,
    }


# --- servicio: precio y variación ---


def test_variacion_close_a_close(conexion):
    guardar_velas(conexion, [vela("GGAL", UN_DIA, 100.0), vela("GGAL", 2 * UN_DIA, 110.0)])
    dato = precio_de_ticker(conexion, "GGAL", "ARS", [], [])
    assert dato == {"cierre": 110.0, "variacion_pct": 10.0}


def test_variacion_negativa(conexion):
    guardar_velas(conexion, [vela("GGAL", UN_DIA, 100.0), vela("GGAL", 2 * UN_DIA, 95.0)])
    dato = precio_de_ticker(conexion, "GGAL", "ARS", [], [])
    assert dato["variacion_pct"] == -5.0


def test_una_sola_vela_no_tiene_variacion(conexion):
    guardar_velas(conexion, [vela("GGAL", UN_DIA, 100.0)])
    dato = precio_de_ticker(conexion, "GGAL", "ARS", [], [])
    assert dato == {"cierre": 100.0, "variacion_pct": None}


def test_ticker_sin_velas_devuelve_none(conexion):
    assert precio_de_ticker(conexion, "GGAL", "ARS", [], []) is None


def test_variacion_en_usd_usa_el_ccl_de_cada_dia(conexion):
    # ARS sube 10% (100→110) pero el dólar también: la variación en USD difiere
    guardar_velas(conexion, [vela("GGAL", UN_DIA, 100.0), vela("GGAL", 2 * UN_DIA, 110.0)])
    guardar_tasas(
        conexion,
        [
            {"fecha": "1970-01-02", "tipo": CCL, "valor": 1000.0},
            {"fecha": "1970-01-03", "tipo": CCL, "valor": 1100.0},
        ],
    )
    fechas = ["1970-01-02", "1970-01-03"]
    valores = [1000.0, 1100.0]
    dato = precio_de_ticker(conexion, "GGAL", "USD", fechas, valores)
    # cierre USD = 110/1100 = 0.1 ; previo USD = 100/1000 = 0.1 → 0% en dólares
    assert dato["cierre"] == 0.1
    assert dato["variacion_pct"] == 0.0


def test_los_tickers_en_usd_que_no_son_byma_no_se_convierten(conexion):
    guardar_velas(conexion, [vela("AAPL", UN_DIA, 200.0), vela("AAPL", 2 * UN_DIA, 210.0)])
    guardar_tasas(conexion, [{"fecha": "1970-01-02", "tipo": CCL, "valor": 1000.0}])
    dato = precio_de_ticker(conexion, "AAPL", "USD", ["1970-01-02"], [1000.0])
    assert dato["cierre"] == 210.0  # sin convertir


def test_calcular_precios_arma_el_diccionario(conexion):
    guardar_velas(
        conexion,
        [
            vela("GGAL", UN_DIA, 100.0),
            vela("GGAL", 2 * UN_DIA, 110.0),
            vela("YPFD", UN_DIA, 50.0),
            vela("YPFD", 2 * UN_DIA, 49.0),
        ],
    )
    precios = calcular_precios(conexion, ["GGAL", "YPFD", "SINDATOS"], "ARS")
    assert precios["GGAL"]["variacion_pct"] == 10.0
    assert precios["YPFD"]["variacion_pct"] == -2.0
    assert "SINDATOS" not in precios  # sin velas: no aparece


# --- endpoint /api/precios ---


def test_endpoint_precios_devuelve_variaciones(cliente, conexion):
    guardar_velas(conexion, [vela("GGAL", UN_DIA, 100.0), vela("GGAL", 2 * UN_DIA, 110.0)])
    datos = cliente.get("/api/precios").json()
    assert datos["GGAL"] == {"cierre": 110.0, "variacion_pct": 10.0}


def test_endpoint_precios_rechaza_moneda_invalida(cliente):
    assert cliente.get("/api/precios", params={"moneda": "EUR"}).status_code == 422


def test_endpoint_precios_default_es_ars(cliente, conexion):
    guardar_velas(conexion, [vela("GGAL", UN_DIA, 100.0), vela("GGAL", 2 * UN_DIA, 110.0)])
    guardar_tasas(conexion, [{"fecha": "1970-01-02", "tipo": CCL, "valor": 1000.0}])
    datos = cliente.get("/api/precios").json()
    assert datos["GGAL"]["cierre"] == 110.0  # ARS, no convertido a USD
