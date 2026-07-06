from unittest.mock import MagicMock

from fastapi.testclient import TestClient

import app.servicios.instalador as instalador
from app.main import app

cliente_api = TestClient(app)


def release_de_github(tag="v9.9.9", assets=None):
    if assets is None:
        assets = [
            {"name": "notas.txt", "browser_download_url": "http://x/notas.txt"},
            {"name": "MOP-9.9.9.dmg", "browser_download_url": "http://x/MOP-9.9.9.dmg"},
        ]
    return {"tag_name": tag, "assets": assets}


def cliente_falso(release):
    cliente = MagicMock()
    respuesta = MagicMock()
    respuesta.raise_for_status.return_value = None
    respuesta.json.return_value = release
    cliente.get.return_value = respuesta
    return cliente


# --- asset_dmg ---


def test_elige_el_asset_dmg_entre_varios():
    asset = instalador.asset_dmg(release_de_github())
    assert asset["name"] == "MOP-9.9.9.dmg"


def test_sin_dmg_devuelve_none():
    assert instalador.asset_dmg({"assets": [{"name": "a.zip"}]}) is None


# --- release_instalable ---


def test_release_mas_nueva_con_dmg_es_instalable():
    info = instalador.release_instalable(cliente_falso(release_de_github()))
    assert info == {
        "version": "9.9.9",
        "url": "http://x/MOP-9.9.9.dmg",
        "nombre": "MOP-9.9.9.dmg",
    }


def test_release_vieja_no_es_instalable():
    info = instalador.release_instalable(cliente_falso(release_de_github(tag="v0.0.1")))
    assert info is None


def test_release_nueva_sin_dmg_no_es_instalable():
    release = release_de_github(assets=[{"name": "codigo.zip"}])
    assert instalador.release_instalable(cliente_falso(release)) is None


def test_sin_red_no_es_instalable():
    cliente = MagicMock()
    cliente.get.side_effect = RuntimeError("sin red")
    assert instalador.release_instalable(cliente) is None


# --- script ayudante ---


def test_ayudante_espera_el_pid_y_reemplaza_la_app(tmp_path):
    ruta = instalador.escribir_ayudante(tmp_path, pid=12345, armado=tmp_path / "armado")
    contenido = ruta.read_text()
    assert "kill -0 12345" in contenido           # espera el cierre real de la app
    assert instalador.RUTA_APP_INSTALADA in contenido
    assert "ditto" in contenido                    # reemplazo conservando atributos
    assert f'open "{instalador.RUTA_APP_INSTALADA}"' in contenido  # relanza
    assert ruta.stat().st_mode & 0o111             # ejecutable


# --- endpoint ---


def test_endpoint_rechaza_en_modo_desarrollo():
    # Sin PyInstaller (sys.frozen) la app corre del repo: no hay .app que pisar
    respuesta = cliente_api.post("/api/actualizacion/instalar")
    assert respuesta.status_code == 409


def test_endpoint_instala_cuando_corre_empaquetada(monkeypatch):
    monkeypatch.setattr("app.routers.actualizacion.empaquetada", lambda: True)
    monkeypatch.setattr(
        "app.routers.actualizacion.instalar_actualizacion",
        lambda: {"instalando": "9.9.9"},
    )
    respuesta = cliente_api.post("/api/actualizacion/instalar")
    assert respuesta.status_code == 200
    assert respuesta.json() == {"instalando": "9.9.9"}


def test_endpoint_sin_version_nueva_devuelve_conflicto(monkeypatch):
    def sin_nueva():
        raise ValueError("No hay una versión nueva instalable")

    monkeypatch.setattr("app.routers.actualizacion.empaquetada", lambda: True)
    monkeypatch.setattr("app.routers.actualizacion.instalar_actualizacion", sin_nueva)
    respuesta = cliente_api.post("/api/actualizacion/instalar")
    assert respuesta.status_code == 409
