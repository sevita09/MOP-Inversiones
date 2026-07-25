"""Backtest rápido: una config sin guardar (la del editor) sobre los últimos meses."""
from datetime import datetime, timedelta, timezone

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


def _sembrar_historia(conexion, dias=400):
    """Velas diarias hasta hoy, oscilando alrededor del umbral de las reglas."""
    hoy = datetime.now(timezone.utc)
    velas = []
    for i in range(dias):
        fecha = hoy - timedelta(days=dias - i)
        precio = 10 + (i % 20)  # cruza 15 seguido: genera entradas y salidas
        velas.append(
            {
                "ticker": "GGAL", "temporalidad": "D", "ts": int(fecha.timestamp()),
                "apertura": precio, "maximo": precio + 1, "minimo": precio - 1,
                "cierre": precio, "volumen": 1000, "es_faltante": 0,
            }
        )
    guardar_velas(conexion, velas)


def _peticion(**cambios):
    base = {"ticker": "GGAL", "temporalidad": "D", "moneda": "ARS", "reglas": REGLAS}
    base.update(cambios)
    return base


def test_backtest_rapido_devuelve_resultado(cliente, conexion):
    _sembrar_historia(conexion)
    respuesta = cliente.post("/api/bots/backtest_rapido", json=_peticion())
    assert respuesta.status_code == 200
    datos = respuesta.json()
    assert datos["estrategia"]["trades"], "tiene que operar"
    assert "metricas" in datos["estrategia"]
    assert "buy_and_hold" in datos


def test_backtest_rapido_respeta_la_ventana_de_meses(cliente, conexion):
    _sembrar_historia(conexion, dias=400)
    un_anio = cliente.post("/api/bots/backtest_rapido", json=_peticion(meses=12)).json()
    un_mes = cliente.post("/api/bots/backtest_rapido", json=_peticion(meses=1)).json()
    # La ventana corta arranca después y tiene menos barras
    assert un_mes["desde"] > un_anio["desde"]
    assert un_mes["estrategia"]["barras"] < un_anio["estrategia"]["barras"]


def test_backtest_rapido_aplica_el_riesgo(cliente, conexion):
    _sembrar_historia(conexion)
    con_stop = cliente.post(
        "/api/bots/backtest_rapido",
        json=_peticion(riesgo={"stop_loss_pct": 5}),
    ).json()
    motivos = {t["motivo"] for t in con_stop["estrategia"]["trades"]}
    assert "stop" in motivos, "con stop al 5% tiene que saltar alguno"


def test_backtest_rapido_sin_entrada_es_422(cliente, conexion):
    _sembrar_historia(conexion)
    sin_entrada = {**REGLAS, "entrada": []}
    assert cliente.post("/api/bots/backtest_rapido", json=_peticion(reglas=sin_entrada)).status_code == 422


def test_backtest_rapido_con_ticker_desconocido_es_422(cliente):
    assert cliente.post("/api/bots/backtest_rapido", json=_peticion(ticker="NADA")).status_code == 422
