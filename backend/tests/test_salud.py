from fastapi.responses import HTMLResponse
from fastapi.testclient import TestClient

from app.main import app

cliente = TestClient(app)


def test_salud_responde_ok():
    respuesta = cliente.get("/api/salud")
    assert respuesta.status_code == 200
    assert respuesta.json() == {"estado": "ok", "servicio": "mop-backend"}


def test_el_html_se_sirve_sin_cache():
    """El WKWebView de la app cacheaba el index.html viejo tras actualizar."""

    @app.get("/pagina_de_prueba", response_class=HTMLResponse)
    def pagina():
        return "<html></html>"

    # Al principio de las rutas: el mount de StaticFiles en "/" (si existe el
    # build del frontend) atraparía la ruta agregada al final
    app.router.routes.insert(0, app.router.routes.pop())

    try:
        respuesta = cliente.get("/pagina_de_prueba")
        assert respuesta.headers["cache-control"] == "no-cache"
        # Las respuestas JSON de la API no llevan el header
        assert "cache-control" not in cliente.get("/api/salud").headers
    finally:
        app.router.routes[:] = [
            ruta for ruta in app.router.routes
            if getattr(ruta, "path", "") != "/pagina_de_prueba"
        ]
