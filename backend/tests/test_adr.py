"""Vista en USD de acciones con ADR: usa el precio del ADR, no la acción ÷ CCL."""
from app.config import SUFIJO_ADR, adr_de
from app.repositorios.tasas_dolar import CCL, guardar_tasas
from app.repositorios.velas import guardar_velas
from app.servicios.descarga import simbolo_yahoo


def vela(ticker, ts, cierre):
    return {
        "ticker": ticker, "temporalidad": "D", "ts": ts,
        "apertura": cierre, "maximo": cierre, "minimo": cierre,
        "cierre": cierre, "volumen": 1000.0,
    }


# --- resolución del símbolo del ADR ---


def test_simbolo_yahoo_resuelve_la_serie_adr():
    assert simbolo_yahoo("SUPV.ADR") == "SUPV"
    assert simbolo_yahoo("PAMP.ADR") == "PAM"
    assert simbolo_yahoo("TECO2.ADR") == "TEO"


def test_adr_de_devuelve_simbolo_y_ratio():
    assert adr_de("SUPV") == {"simbolo": "SUPV", "ratio": 5}
    assert adr_de("PAMP") == {"simbolo": "PAM", "ratio": 25}
    assert adr_de("ALUA") is None  # ALUA no tiene ADR


# --- /api/velas ---


def test_velas_en_usd_usan_el_adr_no_el_ccl(cliente, conexion):
    # La acción local vale 8000 ARS; el ADR vale 9 USD. En USD debe verse el ADR.
    guardar_tasas(conexion, [{"fecha": "1970-01-02", "tipo": CCL, "valor": 1000.0}])
    guardar_velas(conexion, [vela("SUPV", 86400, 8000.0)])
    guardar_velas(conexion, [vela(f"SUPV{SUFIJO_ADR}", 86400, 9.0)])

    usd = cliente.get("/api/velas", params={"ticker": "SUPV", "moneda": "USD"}).json()
    assert usd["velas"][0]["cierre"] == 9.0          # el ADR, no 8000/1000=8
    assert usd["adr"] == {"simbolo": "SUPV", "ratio": 5}


def test_velas_en_ars_usan_la_accion_local(cliente, conexion):
    guardar_velas(conexion, [vela("SUPV", 86400, 8000.0)])
    guardar_velas(conexion, [vela(f"SUPV{SUFIJO_ADR}", 86400, 9.0)])
    ars = cliente.get("/api/velas", params={"ticker": "SUPV", "moneda": "ARS"}).json()
    assert ars["velas"][0]["cierre"] == 8000.0       # la acción local
    assert ars["adr"] == {"simbolo": "SUPV", "ratio": 5}  # la info se informa igual


def test_ticker_sin_adr_no_trae_info(cliente, conexion):
    guardar_velas(conexion, [vela("ALUA", 86400, 100.0)])
    datos = cliente.get("/api/velas", params={"ticker": "ALUA"}).json()
    assert datos["adr"] is None
