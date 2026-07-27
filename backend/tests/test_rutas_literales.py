"""Blindaje de las rutas: ningún literal debe quedar tapado por una paramétrica.

FastAPI resuelve por orden de declaración: si un literal como `/api/bots/algo`
se declara DESPUÉS de `/api/bots/{id_bot}`, la paramétrica lo captura y el
literal empieza a devolver 422 en vez de funcionar. Estos tests fallan apenas
eso pasa, en vez de descubrirlo en producción.
"""
from app.main import app

RUTAS_LITERALES_GET = ["/api/plantillas", "/api/optimizacion"]


def test_las_rutas_literales_responden_su_contenido(cliente):
    """Si una paramétrica las tapara, esto daría 422 en vez de 200."""
    for ruta in RUTAS_LITERALES_GET:
        respuesta = cliente.get(ruta)
        assert respuesta.status_code == 200, f"{ruta} quedó tapada por una ruta paramétrica"


def test_ningun_literal_cuelga_de_una_ruta_con_id_de_bot():
    """La regla estructural: nada literal compite con /api/bots/{id_bot}.

    Mantener los literales fuera de ese espacio (routers propios como
    /api/plantillas y /api/optimizacion) hace imposible el problema de orden.
    """
    conflictivas = []
    for ruta in app.routes:
        path = getattr(ruta, "path", "")
        if not path.startswith("/api/bots/"):
            continue
        segmento = path[len("/api/bots/"):].split("/")[0]
        # El segmento siguiente a /api/bots/ tiene que ser el parámetro del bot
        if not segmento.startswith("{"):
            metodos = getattr(ruta, "methods", set())
            conflictivas.append((path, sorted(metodos)))

    # Los POST no colisionan (no existe POST /api/bots/{id_bot}), pero se listan
    # para que sumar uno nuevo sea una decisión consciente y no un descuido
    permitidas = {"/api/bots/preview", "/api/bots/backtest_rapido"}
    inesperadas = [p for p, _ in conflictivas if p not in permitidas]
    assert not inesperadas, (
        f"Literales nuevos bajo /api/bots/: {inesperadas}. "
        "Ponelos en su propio router (como /api/plantillas) para no depender del orden"
    )


def test_un_texto_nunca_se_confunde_con_un_id_de_bot(cliente):
    """El tipado int del path impide que una palabra devuelva un bot equivocado."""
    respuesta = cliente.get("/api/bots/cualquier_cosa")
    assert respuesta.status_code == 422  # error explícito, nunca datos cruzados
