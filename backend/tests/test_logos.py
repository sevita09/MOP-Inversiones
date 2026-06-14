from unittest.mock import MagicMock

import pytest

import app.servicios.logos as logos


@pytest.fixture
def carpeta_logos(tmp_path, monkeypatch):
    """Aísla la carpeta de logos en un tmp_path por test."""
    monkeypatch.setattr(logos, "CARPETA_LOGOS", tmp_path)
    return tmp_path


def cliente_falso(logoid="apple", status_svg=200, contenido=b"<svg/>"):
    """Cliente httpx simulado: 1ra llamada devuelve el logoid, 2da el SVG."""
    cliente = MagicMock()
    respuesta_logoid = MagicMock()
    respuesta_logoid.json.return_value = {"logoid": logoid}
    respuesta_logoid.raise_for_status.return_value = None
    respuesta_svg = MagicMock()
    respuesta_svg.status_code = status_svg
    respuesta_svg.content = contenido
    cliente.get.side_effect = [respuesta_logoid, respuesta_svg]
    return cliente


# --- símbolo de TradingView ---


def test_simbolo_byma_usa_bcba():
    assert logos.simbolo_tradingview("GGAL") == "BCBA:GGAL"


def test_simbolo_cedear_usa_su_exchange():
    assert logos.simbolo_tradingview("AAPL") == "NASDAQ:AAPL"


def test_simbolo_de_dolar_es_none():
    assert logos.simbolo_tradingview("DOLARCCL") is None
    assert logos.simbolo_tradingview("DOLAROF") is None


# --- logoid ---


def test_obtener_logoid_lee_el_scanner():
    cliente = MagicMock()
    respuesta = MagicMock()
    respuesta.json.return_value = {"logoid": "gpo-fin-galicia"}
    respuesta.raise_for_status.return_value = None
    cliente.get.return_value = respuesta
    assert logos.obtener_logoid("GGAL", cliente) == "gpo-fin-galicia"


def test_obtener_logoid_de_ticker_sin_simbolo_es_none():
    cliente = MagicMock()
    assert logos.obtener_logoid("DOLARCCL", cliente) is None
    cliente.get.assert_not_called()


# --- descarga ---


def test_descargar_logo_guarda_el_svg(carpeta_logos):
    cliente = cliente_falso(logoid="apple", contenido=b"<svg>apple</svg>")
    assert logos.descargar_logo("AAPL", cliente) is True
    assert logos.ruta_logo("AAPL").read_bytes() == b"<svg>apple</svg>"


def test_descargar_logo_sin_logoid_no_escribe(carpeta_logos):
    cliente = MagicMock()
    respuesta = MagicMock()
    respuesta.json.return_value = {"logoid": None}
    respuesta.raise_for_status.return_value = None
    cliente.get.return_value = respuesta
    assert logos.descargar_logo("GGAL", cliente) is False
    assert not logos.tiene_logo("GGAL")


def test_descargar_logo_con_cdn_caido_no_escribe(carpeta_logos):
    cliente = cliente_falso(status_svg=404)
    assert logos.descargar_logo("AAPL", cliente) is False
    assert not logos.tiene_logo("AAPL")


# --- asegurar_logos (auto-descarga de faltantes) ---


def test_asegurar_logos_solo_baja_los_faltantes(carpeta_logos, monkeypatch):
    monkeypatch.setattr(logos, "tickers_con_logo", lambda: ["GGAL", "YPFD", "AAPL"])
    # GGAL ya tiene logo: no debe re-bajarse
    logos.ruta_logo("GGAL").write_bytes(b"<svg/>")

    bajados = []
    monkeypatch.setattr(
        logos, "descargar_logo", lambda ticker, cliente: bajados.append(ticker) or True
    )
    monkeypatch.setattr(logos.httpx, "Client", MagicMock)

    total = logos.asegurar_logos(pausa=0)
    assert total == 2
    assert set(bajados) == {"YPFD", "AAPL"}  # GGAL ya estaba


def test_asegurar_logos_sin_faltantes_no_descarga(carpeta_logos, monkeypatch):
    monkeypatch.setattr(logos, "tickers_con_logo", lambda: ["GGAL"])
    logos.ruta_logo("GGAL").write_bytes(b"<svg/>")
    espia = MagicMock()
    monkeypatch.setattr(logos, "descargar_logo", espia)
    assert logos.asegurar_logos(pausa=0) == 0
    espia.assert_not_called()


def test_asegurar_logos_sigue_si_un_ticker_falla(carpeta_logos, monkeypatch):
    monkeypatch.setattr(logos, "tickers_con_logo", lambda: ["GGAL", "YPFD"])

    def descarga(ticker, cliente):
        if ticker == "GGAL":
            raise RuntimeError("TradingView caído")
        return True

    monkeypatch.setattr(logos, "descargar_logo", descarga)
    monkeypatch.setattr(logos.httpx, "Client", MagicMock)
    assert logos.asegurar_logos(pausa=0) == 1  # YPFD se baja aunque GGAL falle
