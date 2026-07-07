from app.repositorios.tasas_dolar import CCL, guardar_tasas
from app.repositorios.velas import guardar_velas

UN_DIA = 86400


def vela(ts, cierre, ticker="GGAL", temporalidad="D"):
    return {
        "ticker": ticker,
        "temporalidad": temporalidad,
        "ts": ts,
        "apertura": cierre,
        "maximo": cierre,
        "minimo": cierre,
        "cierre": cierre,
        "volumen": 100.0,
    }


def cargar(conexion, cierres, ticker="GGAL", temporalidad="D"):
    guardar_velas(
        conexion,
        [vela((i + 1) * UN_DIA, c, ticker, temporalidad) for i, c in enumerate(cierres)],
    )


def ema_manual(cierres, span):
    alfa = 2 / (span + 1)
    valores = [float(cierres[0])]
    for c in cierres[1:]:
        valores.append(alfa * c + (1 - alfa) * valores[-1])
    return valores


def test_calcula_solo_lo_pedido(cliente, conexion):
    cargar(conexion, [10, 11, 12, 13, 14])
    datos = cliente.get("/api/indicadores", params={"ticker": "GGAL", "incluir": "ema"}).json()
    assert list(datos["indicadores"]) == ["ema"]
    assert len(datos["indicadores"]["ema"]["ema"]) == 5


def test_varios_indicadores_a_la_vez(cliente, conexion):
    cargar(conexion, list(range(1, 40)))
    datos = cliente.get(
        "/api/indicadores", params={"ticker": "GGAL", "incluir": "ema,rsi,macd"}
    ).json()
    assert set(datos["indicadores"]) == {"ema", "rsi", "macd"}
    assert set(datos["indicadores"]["macd"]) == {"macd", "senal", "histograma"}


def test_ts_alineado_con_las_velas(cliente, conexion):
    cargar(conexion, [10, 20, 30])
    datos = cliente.get("/api/indicadores", params={"ticker": "GGAL", "incluir": "ema"}).json()
    assert datos["ts"] == [UN_DIA, 2 * UN_DIA, 3 * UN_DIA]
    assert len(datos["indicadores"]["ema"]["ema"]) == len(datos["ts"])


def test_sin_incluir_devuelve_indicadores_vacios(cliente, conexion):
    cargar(conexion, [10, 20])
    datos = cliente.get("/api/indicadores", params={"ticker": "GGAL"}).json()
    assert datos["indicadores"] == {}


def test_indicador_desconocido_es_422(cliente, conexion):
    cargar(conexion, [10, 20])
    assert cliente.get(
        "/api/indicadores", params={"ticker": "GGAL", "incluir": "noexiste"}
    ).status_code == 422


def test_rechaza_temporalidad_y_moneda_invalidas(cliente):
    assert cliente.get(
        "/api/indicadores", params={"ticker": "GGAL", "temporalidad": "1d"}
    ).status_code == 422
    assert cliente.get(
        "/api/indicadores", params={"ticker": "GGAL", "moneda": "EUR"}
    ).status_code == 422


def test_rechaza_ticker_desconocido(cliente):
    assert cliente.get(
        "/api/indicadores", params={"ticker": "NOEXISTE", "incluir": "ema"}
    ).status_code == 404


def test_bandas_usan_la_ema_central_de_cada_temporalidad(cliente, conexion):
    cierres = list(range(1, 40))
    cargar(conexion, cierres, temporalidad="D")  # EMA central D = 200
    cargar(conexion, cierres, temporalidad="M")  # EMA central M = 12
    diaria = cliente.get(
        "/api/indicadores", params={"ticker": "GGAL", "temporalidad": "D", "incluir": "bandas"}
    ).json()
    mensual = cliente.get(
        "/api/indicadores", params={"ticker": "GGAL", "temporalidad": "M", "incluir": "bandas"}
    ).json()
    media_d = diaria["indicadores"]["bandas"]["media"][-1]
    media_m = mensual["indicadores"]["bandas"]["media"][-1]
    assert media_d == round(ema_manual(cierres, 200)[-1], 6)
    assert media_m == round(ema_manual(cierres, 12)[-1], 6)
    assert media_d != media_m  # cada temporalidad usa su propia ventana


def test_indicadores_en_usd_usan_precios_convertidos(cliente, conexion):
    # ALUA no tiene ADR: en USD se convierte por CCL
    cargar(conexion, [8000.0, 8000.0, 8000.0], ticker="ALUA")
    guardar_tasas(conexion, [{"fecha": "1970-01-02", "tipo": CCL, "valor": 1000.0}])
    ars = cliente.get(
        "/api/indicadores", params={"ticker": "ALUA", "incluir": "ema", "moneda": "ARS"}
    ).json()
    usd = cliente.get(
        "/api/indicadores", params={"ticker": "ALUA", "incluir": "ema", "moneda": "USD"}
    ).json()
    # La EMA en USD es la de ARS dividida por el CCL (8000 → 8.0)
    assert ars["indicadores"]["ema"]["ema"][-1] == 8000.0
    assert usd["indicadores"]["ema"]["ema"][-1] == 8.0
