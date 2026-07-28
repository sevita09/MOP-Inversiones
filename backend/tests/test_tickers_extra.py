import pytest

import app.servicios.tickers_extra as servicio
from app.repositorios.tickers_extra import listar, simbolo_de


@pytest.fixture
def yahoo_conoce(monkeypatch):
    """Simula qué símbolos existen en Yahoo Finance."""

    def configurar(*simbolos):
        monkeypatch.setattr(servicio, "probar_simbolo", lambda s: s in simbolos)

    return configurar


@pytest.fixture
def sin_sync_ni_logo(monkeypatch):
    """Evita el sync y la descarga de logo reales en los tests de endpoints."""
    monkeypatch.setattr(
        "app.routers.tickers_extra.sincronizar_en_background", lambda: False
    )
    monkeypatch.setattr(
        "app.routers.tickers_extra.descargar_logo_extra_en_background",
        lambda ticker, grupo: None,
    )


# --- resolución de símbolo según el grupo ---


def test_panel_byma_resuelve_con_sufijo_ba(yahoo_conoce):
    yahoo_conoce("HARG.BA")
    assert servicio.resolver_simbolo("HARG", "panel_general") == "HARG.BA"


def test_cedear_usa_el_subyacente_crudo(yahoo_conoce):
    yahoo_conoce("TESTX.BA", "TESTX")
    assert servicio.resolver_simbolo("TESTX", "cedears") == "TESTX"


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
    yahoo_conoce("TESTX")
    resultado = servicio.agregar_ticker(conexion, " testx ", "cedears")
    assert resultado == {"ticker": "TESTX", "simbolo_yf": "TESTX", "grupo": "cedears"}
    assert simbolo_de(conexion, "TESTX") == "TESTX"


def test_rechaza_grupo_invalido(conexion, yahoo_conoce):
    yahoo_conoce("TESTX")
    with pytest.raises(ValueError, match="Grupo inválido"):
        servicio.agregar_ticker(conexion, "TESTX", "otros")


def test_rechaza_ticker_del_universo_fijo(conexion, yahoo_conoce):
    yahoo_conoce("GGAL.BA")
    with pytest.raises(ValueError, match="ya está en la app"):
        servicio.agregar_ticker(conexion, "GGAL", "panel_lider")


def test_rechaza_ticker_ya_agregado(conexion, yahoo_conoce):
    yahoo_conoce("TESTX")
    servicio.agregar_ticker(conexion, "TESTX", "cedears")
    with pytest.raises(ValueError, match="ya fue agregado"):
        servicio.agregar_ticker(conexion, "TESTX", "cedears")


def test_rechaza_ticker_desconocido_en_yahoo(conexion, yahoo_conoce):
    yahoo_conoce()
    with pytest.raises(ValueError, match="no se encontró"):
        servicio.agregar_ticker(conexion, "ZZZZ", "cedears")


# --- endpoints ---


def test_endpoint_agrega_y_se_suma_a_su_grupo(cliente, yahoo_conoce, sin_sync_ni_logo):
    yahoo_conoce("TESTX")
    respuesta = cliente.post(
        "/api/tickers_extra", json={"ticker": "TESTX", "grupo": "cedears"}
    )
    assert respuesta.status_code == 201
    grupos = cliente.get("/api/tickers").json()
    assert "TESTX" in grupos["cedears"]
    assert "agregados" not in grupos


def test_endpoint_crea_grupos_indices_y_cripto(cliente, yahoo_conoce, sin_sync_ni_logo):
    yahoo_conoce("^MERV", "BTC-USD")
    cliente.post("/api/tickers_extra", json={"ticker": "MERV", "grupo": "indices"})
    cliente.post("/api/tickers_extra", json={"ticker": "BTC", "grupo": "cripto"})
    grupos = cliente.get("/api/tickers").json()
    assert grupos["indices"] == ["MERVAL", "MERV"]  # MERVAL es fijo de config
    assert grupos["cripto"] == ["BTC"]


def test_endpoint_rechaza_invalido(cliente, yahoo_conoce, sin_sync_ni_logo):
    yahoo_conoce()
    respuesta = cliente.post(
        "/api/tickers_extra", json={"ticker": "ZZZZ", "grupo": "cedears"}
    )
    assert respuesta.status_code == 422


def test_endpoint_elimina(cliente, conexion, yahoo_conoce, sin_sync_ni_logo):
    yahoo_conoce("TESTX")
    cliente.post("/api/tickers_extra", json={"ticker": "TESTX", "grupo": "cedears"})
    assert cliente.delete("/api/tickers_extra/testx").status_code == 200
    assert listar(conexion) == []
    assert cliente.delete("/api/tickers_extra/TESTX").status_code == 404


def test_ticker_agregado_vale_para_categorias_y_velas(
    cliente, yahoo_conoce, sin_sync_ni_logo
):
    yahoo_conoce("TESTX")
    cliente.post("/api/tickers_extra", json={"ticker": "TESTX", "grupo": "cedears"})

    id_cat = cliente.post("/api/categorias", json={"nombre": "Tech"}).json()["id"]
    assert (
        cliente.post(f"/api/categorias/{id_cat}/tickers", json={"ticker": "TESTX"}).status_code
        == 201
    )
    # /api/velas lo reconoce (sin datos todavía, pero ya no es "desconocido")
    assert cliente.get("/api/velas?ticker=TESTX").status_code == 200


# --- conversión a USD de agregados BYMA (.BA) ---


def test_extra_byma_se_convierte_a_usd(conexion, yahoo_conoce):
    from app.servicios.dolar import se_convierte_a_usd

    yahoo_conoce("HARG.BA")
    servicio.agregar_ticker(conexion, "HARG", "panel_general")
    assert se_convierte_a_usd("HARG", conexion)
    # Un cedear agregado (subyacente USD) no se convierte
    yahoo_conoce("TESTX")
    servicio.agregar_ticker(conexion, "TESTX", "cedears")
    assert not se_convierte_a_usd("TESTX", conexion)


def test_indicadores_y_niveles_reconocen_al_agregado(
    cliente, yahoo_conoce, sin_sync_ni_logo
):
    yahoo_conoce("TESTX")
    cliente.post("/api/tickers_extra", json={"ticker": "TESTX", "grupo": "cedears"})
    # Sin velas devuelven series vacías, pero ya no "Ticker desconocido"
    assert cliente.get("/api/indicadores?ticker=TESTX&incluir=ema").status_code == 200
    assert cliente.get("/api/niveles_swing?ticker=TESTX").status_code == 200
