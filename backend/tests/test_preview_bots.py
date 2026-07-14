import pytest

from app.repositorios.velas import guardar_velas


@pytest.fixture
def velas_ggal(conexion):
    """Historia diaria sintética de GGAL: salta de 10 a 30 en la barra 3."""
    cierres = [10, 15, 30, 32]
    guardar_velas(
        conexion,
        [
            {
                "ticker": "GGAL",
                "temporalidad": "D",
                "ts": (i + 1) * 100,
                "apertura": c,
                "maximo": c + 1,
                "minimo": c - 1,
                "cierre": c,
                "volumen": 1000,
                "es_faltante": 0,
            }
            for i, c in enumerate(cierres)
        ],
    )


REGLAS = {
    "version": 1,
    "entrada": [
        {
            "indicador": "ema",
            "serie": "ema",
            "operador": "cruza_arriba",
            "objetivo": 20,
            "params": {"periodo": 1},
        }
    ],
    "salida": [],
    "filtros": [],
}


def _peticion(**cambios):
    base = {"ticker": "GGAL", "temporalidad": "D", "moneda": "ARS", "reglas": REGLAS}
    base.update(cambios)
    return base


def test_preview_devuelve_los_ts_donde_dispara(cliente, velas_ggal):
    respuesta = cliente.post("/api/bots/preview", json=_peticion())
    assert respuesta.status_code == 200
    assert respuesta.json() == {"ts_entrada": [300], "ts_salida": []}


def test_preview_con_ticker_desconocido_es_422(cliente):
    assert cliente.post("/api/bots/preview", json=_peticion(ticker="NADA")).status_code == 422


def test_preview_con_temporalidad_horaria_es_422(cliente, velas_ggal):
    assert (
        cliente.post("/api/bots/preview", json=_peticion(temporalidad="H")).status_code == 422
    )


def test_preview_con_reglas_invalidas_es_422(cliente, velas_ggal):
    reglas = {**REGLAS, "entrada": [{"indicador": "magia", "serie": "x", "operador": "mayor", "objetivo": 1}]}
    assert cliente.post("/api/bots/preview", json=_peticion(reglas=reglas)).status_code == 422


def test_preview_sin_velas_devuelve_vacio(cliente):
    respuesta = cliente.post("/api/bots/preview", json=_peticion())
    assert respuesta.status_code == 200
    assert respuesta.json() == {"ts_entrada": [], "ts_salida": []}
