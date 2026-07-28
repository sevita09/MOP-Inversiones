"""El índice MERVAL (^MERV): un papel más del universo, pero en pesos.

Es el benchmark de mercado de la cartera (v7.1), así que tiene que bajarse con
el símbolo correcto, convertirse a USD con el CCL y compartir el calendario de
ruedas con los papeles BYMA.
"""
from app.config import INDICES_LOCALES, tickers_byma, tickers_en_pesos, todos_los_tickers
from app.servicios.descarga import simbolo_yahoo
from app.servicios.dolar import se_convierte_a_usd
from app.servicios.reparador import companeros_de_mercado


def test_el_simbolo_de_yahoo_es_merv():
    """No es MERVAL.BA: los índices tienen su propio símbolo con ^."""
    assert INDICES_LOCALES["MERVAL"] == "^MERV"
    assert simbolo_yahoo("MERVAL") == "^MERV"


def test_entra_al_universo_que_se_sincroniza():
    assert "MERVAL" in todos_los_tickers()
    assert "MERVAL" not in tickers_byma()  # no es un papel: no lleva sufijo .BA


def test_cotiza_en_pesos_y_se_convierte_a_usd():
    """El 'Merval en dólares' es el índice dividido por el CCL de cada rueda."""
    assert "MERVAL" in tickers_en_pesos()
    assert se_convierte_a_usd("MERVAL")


def test_comparte_el_calendario_de_ruedas_con_byma():
    """Opera los mismos días que los papeles locales: un feriado no es un hueco."""
    companeros = companeros_de_mercado("MERVAL")
    assert "GGAL" in companeros
    assert "AAPL" not in companeros
    assert "MERVAL" in companeros_de_mercado("GGAL")


def test_aparece_en_el_grupo_indices(cliente):
    assert "MERVAL" in cliente.get("/api/tickers").json()["indices"]
