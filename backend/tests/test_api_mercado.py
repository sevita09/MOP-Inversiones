import time
from unittest.mock import patch

import app.servicios.dolar as dolar
import app.servicios.sincronizador as sincronizador
from app.config import PANEL_GENERAL, PANEL_LIDER
from app.repositorios.tasas_dolar import CCL, guardar_tasas
from app.repositorios.velas import guardar_velas

UN_DIA = 86400


def vela(ts, cierre=100.0):
    return {
        "ticker": "GGAL",
        "temporalidad": "D",
        "ts": ts,
        "apertura": cierre,
        "maximo": cierre,
        "minimo": cierre,
        "cierre": cierre,
        "volumen": 1000.0,
    }


def esperar_fin_de_sync(timeout=2.0):
    limite = time.time() + timeout
    while sincronizador.hay_sync_en_curso() and time.time() < limite:
        time.sleep(0.01)


def test_tickers_devuelve_los_paneles(cliente):
    datos = cliente.get("/api/tickers").json()
    assert datos["panel_lider"] == PANEL_LIDER
    assert datos["panel_general"] == PANEL_GENERAL
    assert "GGALD" not in datos["panel_lider"] + datos["panel_general"] + datos["cedears"]


def test_velas_devuelve_las_guardadas(cliente, conexion):
    guardar_velas(conexion, [vela(UN_DIA), vela(2 * UN_DIA, cierre=105.0)])
    datos = cliente.get("/api/velas", params={"ticker": "GGAL", "temporalidad": "D"}).json()
    assert datos["ticker"] == "GGAL"
    assert [v["cierre"] for v in datos["velas"]] == [100.0, 105.0]


def test_velas_filtra_por_rango(cliente, conexion):
    guardar_velas(conexion, [vela(i * UN_DIA) for i in range(1, 6)])
    datos = cliente.get(
        "/api/velas",
        params={"ticker": "GGAL", "temporalidad": "D", "desde": 2 * UN_DIA, "hasta": 4 * UN_DIA},
    ).json()
    assert [v["ts"] for v in datos["velas"]] == [2 * UN_DIA, 3 * UN_DIA, 4 * UN_DIA]


def test_velas_rechaza_temporalidad_invalida(cliente):
    respuesta = cliente.get("/api/velas", params={"ticker": "GGAL", "temporalidad": "1d"})
    assert respuesta.status_code == 422


def test_velas_rechaza_ticker_desconocido(cliente):
    respuesta = cliente.get("/api/velas", params={"ticker": "NOEXISTE"})
    assert respuesta.status_code == 404


def test_velas_en_usd_divide_por_el_ccl(cliente, conexion):
    guardar_tasas(conexion, [{"fecha": "1970-01-02", "tipo": CCL, "valor": 1000.0}])
    guardar_velas(conexion, [vela(UN_DIA, cierre=8000.0)])
    datos = cliente.get("/api/velas", params={"ticker": "GGAL", "moneda": "USD"}).json()
    assert datos["moneda"] == "USD"
    assert datos["velas"][0]["cierre"] == 8.0


def test_velas_ars_es_el_default(cliente, conexion):
    guardar_velas(conexion, [vela(UN_DIA, cierre=8000.0)])
    datos = cliente.get("/api/velas", params={"ticker": "GGAL"}).json()
    assert datos["moneda"] == "ARS"
    assert datos["velas"][0]["cierre"] == 8000.0


def test_velas_rechaza_moneda_invalida(cliente):
    respuesta = cliente.get("/api/velas", params={"ticker": "GGAL", "moneda": "EUR"})
    assert respuesta.status_code == 422


def test_velas_acepta_tickers_de_dolar(cliente, conexion):
    guardar_velas(conexion, [dict(vela(UN_DIA, cierre=1450.0), ticker="DOLARCCL")])
    datos = cliente.get("/api/velas", params={"ticker": "DOLARCCL"}).json()
    assert datos["velas"][0]["cierre"] == 1450.0


def test_sync_lanza_y_publica_el_resumen(cliente, conexion):
    resumen = {"velas_guardadas": 3, "pares_sincronizados": 1, "velas_refrescadas": 0, "errores": []}
    with patch.object(sincronizador, "sincronizar_todo", return_value=dict(resumen)), \
         patch.object(sincronizador, "obtener_conexion", return_value=conexion), \
         patch.object(dolar, "descargar_velas", return_value=[]):  # nunca tocar la red
        assert cliente.post("/api/sync").json() == {"estado": "iniciado"}
        esperar_fin_de_sync()

    publicado = cliente.get("/api/sync").json()["ultimo_resumen"]
    assert publicado["velas_guardadas"] == 3
    assert "reparacion" in publicado and "ccl" in publicado and "dolar_oficial" in publicado


def test_sync_rechaza_si_ya_hay_uno_corriendo(cliente, conexion):
    def sync_lento(conexion, ahora=None):
        time.sleep(0.2)
        return {"velas_guardadas": 0, "pares_sincronizados": 0, "velas_refrescadas": 0, "errores": []}

    with patch.object(sincronizador, "sincronizar_todo", sync_lento), \
         patch.object(sincronizador, "obtener_conexion", return_value=conexion), \
         patch.object(dolar, "descargar_velas", return_value=[]):  # nunca tocar la red
        assert cliente.post("/api/sync").json() == {"estado": "iniciado"}
        assert cliente.post("/api/sync").json() == {"estado": "ya_en_curso"}
        assert cliente.get("/api/sync").json()["en_curso"] is True
        esperar_fin_de_sync()
