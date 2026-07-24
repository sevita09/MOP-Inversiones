from app.repositorios.velas import guardar_velas

REGLAS = {
    "version": 1,
    "entrada": [
        {"indicador": "ema", "serie": "ema", "operador": "mayor", "objetivo": 15, "params": {"periodo": 1}}
    ],
    "salida": [
        {"indicador": "ema", "serie": "ema", "operador": "menor", "objetivo": 15, "params": {"periodo": 1}}
    ],
    "filtros": [],
}


def _sembrar(conexion, precios, ticker="GGAL"):
    guardar_velas(
        conexion,
        [
            {"ticker": ticker, "temporalidad": "D", "ts": (i + 1) * 86400, "apertura": p,
             "maximo": p + 1, "minimo": p - 1, "cierre": p, "volumen": 1000, "es_faltante": 0}
            for i, p in enumerate(precios)
        ],
    )


def test_backtest_por_bot(cliente, conexion):
    _sembrar(conexion, [10, 12, 20, 25, 18, 12, 30])
    bot = cliente.post(
        "/api/bots",
        json={"nombre": "Bt", "ticker": "GGAL", "temporalidad": "D", "reglas": REGLAS},
    ).json()

    respuesta = cliente.get(f"/api/bots/{bot['id']}/backtest")
    assert respuesta.status_code == 200
    datos = respuesta.json()
    assert "estrategia" in datos and "buy_and_hold" in datos
    assert datos["estrategia"]["capital_inicial"] == 1000000
    assert isinstance(datos["estrategia"]["trades"], list)
    assert isinstance(datos["estrategia"]["curva"], list)


def test_backtest_de_bot_inexistente_es_404(cliente):
    assert cliente.get("/api/bots/999/backtest").status_code == 404


def test_backtest_sin_reglas_de_entrada_es_422(cliente, conexion):
    _sembrar(conexion, [10, 20])
    bot = cliente.post(
        "/api/bots", json={"nombre": "Vacio", "ticker": "GGAL", "temporalidad": "D"}
    ).json()
    assert cliente.get(f"/api/bots/{bot['id']}/backtest").status_code == 422


def test_backtest_respeta_el_rango(cliente, conexion):
    _sembrar(conexion, [10, 12, 20, 25, 18, 12, 30])
    bot = cliente.post(
        "/api/bots",
        json={"nombre": "Bt2", "ticker": "GGAL", "temporalidad": "D", "reglas": REGLAS},
    ).json()
    # Solo desde la barra 4 (ts 4*86400) en adelante
    respuesta = cliente.get(f"/api/bots/{bot['id']}/backtest?desde={4 * 86400}").json()
    assert respuesta["desde"] == 4 * 86400
