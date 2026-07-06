"""MOP como app de escritorio.

Levanta el backend embebido (uvicorn en un hilo daemon) y abre una ventana nativa
que carga la app servida en ese mismo puerto. Al cerrar la ventana el proceso
termina y con él el backend: no queda ningún `localhost` colgado.

Correr desde `backend/` con el venv activo:  python escritorio.py
"""
from __future__ import annotations

import threading
import time
import urllib.request

import uvicorn
import webview

from app.canal import CANAL
from app.main import app

HOST = "localhost"  # mismo origen que usa el cliente del frontend (evita CORS)
# La app dev usa otro puerto: puede correr a la par de la instalada
PORT = 8100 if CANAL == "dev" else 8000
TITULO = "MOP Inversiones (DEV)" if CANAL == "dev" else "MOP Inversiones"


def _levantar_backend() -> uvicorn.Server:
    config = uvicorn.Config(app, host=HOST, port=PORT, log_level="warning")
    server = uvicorn.Server(config)
    # No corre en el hilo principal: uvicorn no puede instalar signal handlers ahí
    server.install_signal_handlers = lambda: None
    threading.Thread(target=server.run, daemon=True).start()
    return server


def _esperar_backend(intentos: int = 100) -> bool:
    url = f"http://{HOST}:{PORT}/api/salud"
    for _ in range(intentos):
        try:
            with urllib.request.urlopen(url, timeout=0.5):
                return True
        except Exception:
            time.sleep(0.1)
    return False


def main() -> None:
    server = _levantar_backend()
    if not _esperar_backend():
        raise RuntimeError("El backend no respondió a tiempo")
    webview.create_window(
        TITULO,
        f"http://{HOST}:{PORT}",
        width=1400,
        height=900,
        min_size=(900, 600),
    )
    webview.start()  # bloquea hasta que se cierra la ventana
    server.should_exit = True  # frena el backend (el hilo es daemon igual)


if __name__ == "__main__":
    main()
