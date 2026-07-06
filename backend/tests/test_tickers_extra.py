import pytest

import app.servicios.tickers_extra as servicio
from app.repositorios.tickers_extra import listar, simbolo_de


@pytest.fixture
def yahoo_conoce(monkeypatch):
    """Simula qué símbolos existen en Yahoo Finance."""

    def configurar(*simbolos):
        monkeypatch.setattr(servicio, "probar_simbolo", lambda s: s in simbolos)

    return configurar


# --- resolución de símbolo según el grupo ---


def test_panel_byma_resuelve_con_sufijo_ba(yahoo_conoce):
    yahoo_conoce("HARG.BA")
    assert servicio.resolver_simbolo("HARG", "panel_general") == "HARG.BA"


def test_cedear_usa_el_subyacente_crudo(yahoo_conoce):
    yahoo_conoce("MSFT.BA", "MSFT")
    assert servicio.resolver_simbolo("MSFT", "cedears") == "MSFT"


def test_indice_prueba_con_acento_circunflejo(yahoo_conoce):
    yahoo_conoce("^MERV")
    assert servicio.resolver_simbolo("MERV", "indices") == "^MERV"


def test_cripto_prueba_el_par_contra_usd(yahoo_conoce):
    yahoo_conoce("BTC-USD")
    assert servicio.resolver_simbolo("BTC", "cripto") == "BTC-USD"


def test_simbolo_inexistente_devuelve_none(yahoo_conoce):
    yahoo_conoce()
    assert servicio.resolver_simbolo("NOEXISTE", "cedears") is None


# --- agregar ticker (servicio) ---


def test_agrega_ticker_valido(conexion, yahoo_conoce):
    yahoo_conoce("MSFT")
    resultado = servicio.agregar_ticker(conexion, " msft ", "cedears")
    assert resultado == {"ticker": "MSFT", "simbolo_yf": "MSFT", "grupo": "cedears"}
    assert simbolo_de(conexion, "MSFT") == "MSFT"


def test_rechaza_grupo_invalido(conexion, yahoo_conoce):
    yahoo_conoce("MSFT")
    with pytest.raises(ValueError, match="Grupo inválido"):
        servicio.agregar_ticker(conexion, "MSFT", "otros")


def test_rechaza_ticker_del_universo_fijo(conexion, yahoo_conoce):
    yahoo_conoce("GGAL.BA")
    with pytest.raises(ValueError, match="ya está en la app"):
        servicio.agregar_ticker(conexion, "GGAL", "panel_lider")


def test_rechaza_ticker_ya_agregado(conexion, yahoo_conoce):
    yahoo_conoce("MSFT")
    servicio.agregar_ticker(conexion, "MSFT", "cedears")
    with pytest.raises(ValueError, match="ya fue agregado"):
        servicio.agregar_ticker(conexion, "MSFT", "cedears")


def test_rechaza_ticker_desconocido_en_yahoo(conexion, yahoo_conoce):
    yahoo_conoce()
    with pytest.raises(ValueError, match="no se encontró"):
        servicio.agregar_ticker(conexion, "ZZZZ", "cedears")
