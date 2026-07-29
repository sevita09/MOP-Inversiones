"""Dólar MEP (GGAL contra GGALD.BA) y la ventana de consulta del IPC."""
from datetime import datetime

from app.config import (
    SIMBOLO_MEP_BASE,
    TICKER_MEP_BASE,
    tickers_de_la_rueda_local,
    tickers_en_pesos,
    todos_los_tickers,
)
from app.repositorios import configuracion as repo_config
from app.repositorios.tasas_dolar import MEP, obtener_tasas
from app.repositorios.velas import guardar_velas
from app.servicios.cartera import TIPO_DOLAR
from app.servicios.descarga import simbolo_yahoo
from app.servicios.dolar import se_convierte_a_usd, sincronizar_mep
from app.servicios.inflacion import (
    CLAVE_ULTIMO_INTENTO,
    corresponde_consultar,
    guardar_inflacion,
    indice_alineado,
)
from app.servicios.reparador import companeros_de_mercado

UN_DIA = 86400


def _vela(conexion, ticker, ts, cierre, es_faltante=0):
    guardar_velas(
        conexion,
        [{"ticker": ticker, "temporalidad": "D", "ts": ts, "apertura": cierre,
          "maximo": cierre, "minimo": cierre, "cierre": cierre, "volumen": 100.0,
          "es_faltante": es_faltante}],
    )


# --- MEP ---


def test_el_simbolo_de_yahoo_de_la_punta_en_dolares():
    assert simbolo_yahoo(TICKER_MEP_BASE) == SIMBOLO_MEP_BASE == "GGALD.BA"
    assert TICKER_MEP_BASE in todos_los_tickers()


def test_la_punta_en_dolares_no_se_convierte():
    """GGALD.BA ya cotiza en dólares: convertirla sería dividir dos veces."""
    assert not se_convierte_a_usd(TICKER_MEP_BASE)
    assert TICKER_MEP_BASE not in tickers_en_pesos()


def test_comparte_calendario_con_la_rueda_local():
    """Opera en BYMA aunque liquide en dólares: sus feriados son los de acá."""
    assert TICKER_MEP_BASE in tickers_de_la_rueda_local()
    assert "GGAL" in companeros_de_mercado(TICKER_MEP_BASE)
    assert "AAPL" not in companeros_de_mercado(TICKER_MEP_BASE)


def test_el_mep_es_la_accion_en_pesos_sobre_la_accion_en_dolares(conexion):
    """Sin ratio: es la misma acción de los dos lados (el CCL sí lleva ×10)."""
    _vela(conexion, "GGAL", UN_DIA, 7855.0)
    _vela(conexion, TICKER_MEP_BASE, UN_DIA, 5.13)

    assert sincronizar_mep(conexion) == 1
    tasas = obtener_tasas(conexion, MEP)
    assert round(tasas[0]["valor"]) == 1531  # 7855 / 5,13


def test_un_placeholder_no_pisa_la_rueda_real(conexion):
    """El reparador deja placeholders con otra hora: no pueden tapar el dato."""
    _vela(conexion, "GGAL", UN_DIA, 7855.0)
    _vela(conexion, TICKER_MEP_BASE, UN_DIA, 5.13)
    _vela(conexion, TICKER_MEP_BASE, UN_DIA + 3600, 0.0, es_faltante=1)

    assert sincronizar_mep(conexion) == 1  # la rueda sobrevive


def test_la_cartera_se_valua_con_mep():
    assert TIPO_DOLAR == MEP


# --- ventana de consulta del IPC ---


def test_sin_datos_se_consulta_siempre(conexion):
    """La carga inicial no espera a la ventana."""
    assert corresponde_consultar(conexion, datetime(2026, 7, 28, 10))


def test_fuera_de_la_ventana_no_se_consulta(conexion):
    guardar_inflacion(conexion, [{"fecha": "2026-06-30", "valor": 1.9}])
    assert not corresponde_consultar(conexion, datetime(2026, 7, 28, 10))
    assert not corresponde_consultar(conexion, datetime(2026, 7, 10, 10))
    assert not corresponde_consultar(conexion, datetime(2026, 7, 16, 10))


def test_dentro_de_la_ventana_se_consulta_una_vez_por_hora(conexion):
    guardar_inflacion(conexion, [{"fecha": "2026-06-30", "valor": 1.9}])
    assert corresponde_consultar(conexion, datetime(2026, 7, 13, 10))

    repo_config.guardar(conexion, CLAVE_ULTIMO_INTENTO, datetime(2026, 7, 13, 10).isoformat())
    assert not corresponde_consultar(conexion, datetime(2026, 7, 13, 10, 45))
    assert corresponde_consultar(conexion, datetime(2026, 7, 13, 11, 5))


# --- índice de inflación ---


def test_el_indice_encadena_los_meses(conexion):
    """2% y después 3% no es 5%: es 1,02 × 1,03."""
    guardar_inflacion(
        conexion,
        [{"fecha": "2026-01-31", "valor": 2.0}, {"fecha": "2026-02-28", "valor": 3.0}],
    )
    indices = indice_alineado(conexion, ["2026-01-15", "2026-02-10", "2026-03-10"])
    assert indices[0] is None  # antes del primer cierre no hay índice
    assert round(indices[1], 4) == 1.02
    assert round(indices[2], 4) == 1.0506
