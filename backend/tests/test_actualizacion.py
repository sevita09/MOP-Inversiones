from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

import app.servicios.actualizacion as actualizacion
from app.main import app
from app.version import VERSION


@pytest.fixture(autouse=True)
def cache_limpia():
    """Cada test arranca sin resultado cacheado."""
    actualizacion.limpiar_cache()
    yield
    actualizacion.limpiar_cache()


def cliente_falso(tags=None, falla=False):
    """Cliente httpx simulado que responde la lista de tags de GitHub."""
    cliente = MagicMock()
    if falla:
        cliente.get.side_effect = RuntimeError("sin red")
        return cliente
    respuesta = MagicMock()
    respuesta.raise_for_status.return_value = None
    respuesta.json.return_value = [{"name": nombre} for nombre in (tags or [])]
    cliente.get.return_value = respuesta
    return cliente


# --- parsear_version ---


def test_parsea_version_con_y_sin_prefijo_v():
    assert actualizacion.parsear_version("v3.1.0") == (3, 1, 0)
    assert actualizacion.parsear_version("3.10.2") == (3, 10, 2)


def test_rechaza_textos_que_no_son_version():
    assert actualizacion.parsear_version("main") is None
    assert actualizacion.parsear_version("v3.1") is None
    assert actualizacion.parsear_version("v3.1.beta") is None


# --- ultima_version_publicada ---


def test_devuelve_el_tag_mas_alto():
    cliente = cliente_falso(tags=["v3.1.0", "v2.6.0", "v3.0.1"])
    assert actualizacion.ultima_version_publicada(cliente) == "3.1.0"


def test_ignora_tags_que_no_son_version():
    cliente = cliente_falso(tags=["experimento", "v1.2.0"])
    assert actualizacion.ultima_version_publicada(cliente) == "1.2.0"


def test_sin_red_devuelve_none():
    assert actualizacion.ultima_version_publicada(cliente_falso(falla=True)) is None


# --- estado_actualizacion ---


def test_avisa_cuando_hay_version_mas_nueva(monkeypatch):
    monkeypatch.setattr(actualizacion, "VERSION", "3.1.0")
    estado = actualizacion.estado_actualizacion(cliente_falso(tags=["v9.0.0"]))
    assert estado["hay_nueva"] is True
    assert estado["ultima"] == "9.0.0"
    assert estado["actual"] == "3.1.0"
    assert "github.com" in estado["url_descarga"]


def test_no_avisa_cuando_esta_al_dia(monkeypatch):
    monkeypatch.setattr(actualizacion, "VERSION", "3.2.0")
    estado = actualizacion.estado_actualizacion(cliente_falso(tags=["v3.2.0", "v3.1.0"]))
    assert estado["hay_nueva"] is False


def test_sin_red_no_avisa_ni_rompe():
    estado = actualizacion.estado_actualizacion(cliente_falso(falla=True))
    assert estado["hay_nueva"] is False
    assert estado["ultima"] is None


def test_cachea_el_resultado_pero_no_los_fallos():
    con_red = cliente_falso(tags=["v0.0.1"])

    # Un fallo no queda cacheado: la próxima consulta reintenta
    actualizacion.estado_actualizacion(cliente_falso(falla=True))
    assert actualizacion.estado_actualizacion(con_red)["ultima"] == "0.0.1"

    # Con resultado cacheado, no se vuelve a consultar
    otro = cliente_falso(tags=["v9.9.9"])
    assert actualizacion.estado_actualizacion(otro)["ultima"] == "0.0.1"
    otro.get.assert_not_called()


# --- endpoints ---

cliente_api = TestClient(app)


def test_endpoint_version_informa_la_version():
    respuesta = cliente_api.get("/api/version")
    assert respuesta.status_code == 200
    assert respuesta.json() == {"version": VERSION, "canal": "prod"}


def test_endpoint_actualizacion(monkeypatch):
    monkeypatch.setattr(
        "app.routers.actualizacion.estado_actualizacion",
        lambda: {"actual": "3.2.0", "ultima": "3.3.0", "hay_nueva": True, "url_descarga": "x"},
    )
    respuesta = cliente_api.get("/api/actualizacion")
    assert respuesta.status_code == 200
    assert respuesta.json()["hay_nueva"] is True
