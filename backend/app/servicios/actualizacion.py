"""Aviso de versión nueva contra los tags publicados en GitHub.

La app conoce su versión (`app/version.py`) y consulta la API pública de GitHub
(sin token). Si el tag `vX.Y.Z` más alto supera a la versión propia, hay una
actualización disponible: se informa con el link de descarga. No se
auto-actualiza — solo avisa.
"""
from __future__ import annotations

import threading
import time
from typing import Optional

import httpx

from app.version import VERSION

REPO_GITHUB = "sevita09/MOP-Inversiones"
URL_TAGS = f"https://api.github.com/repos/{REPO_GITHUB}/tags"
URL_DESCARGA = f"https://github.com/{REPO_GITHUB}/releases"

# GitHub limita a 60 consultas por hora sin token y los tags no cambian seguido,
# así que el resultado se cachea. Los fallos no se cachean: se reintenta.
TTL_CACHE_SEGUNDOS = 3600.0
_cache: dict = {"resultado": None, "expira": 0.0}
_lock = threading.Lock()


def parsear_version(texto: str) -> Optional[tuple[int, int, int]]:
    """"v3.1.0" o "3.1.0" → (3, 1, 0). None si no es una versión semántica."""
    partes = texto.strip().lstrip("v").split(".")
    if len(partes) != 3:
        return None
    try:
        numeros = tuple(int(parte) for parte in partes)
    except ValueError:
        return None
    return numeros  # type: ignore[return-value]


def ultima_version_publicada(cliente: Optional[httpx.Client] = None) -> Optional[str]:
    """El tag de versión más alto del repo, sin la "v". None si no se pudo consultar."""
    try:
        propio = cliente or httpx.Client(timeout=5)
        try:
            respuesta = propio.get(URL_TAGS)
            respuesta.raise_for_status()
            nombres = [tag.get("name", "") for tag in respuesta.json()]
        finally:
            if cliente is None:
                propio.close()
    except Exception:
        return None

    versiones = [numeros for nombre in nombres if (numeros := parsear_version(nombre))]
    if not versiones:
        return None
    return ".".join(str(numero) for numero in max(versiones))


def estado_actualizacion(cliente: Optional[httpx.Client] = None) -> dict:
    """Versión actual, última publicada y si conviene actualizar (cacheado)."""
    from app.canal import CANAL

    if CANAL == "dev":
        # La app de pruebas no se actualiza sola: se reconstruye desde el código
        return {
            "actual": VERSION,
            "ultima": None,
            "hay_nueva": False,
            "url_descarga": URL_DESCARGA,
        }
    ahora = time.time()
    with _lock:
        if _cache["resultado"] is not None and ahora < _cache["expira"]:
            return _cache["resultado"]

    ultima = ultima_version_publicada(cliente)
    hay_nueva = ultima is not None and parsear_version(ultima) > parsear_version(VERSION)
    resultado = {
        "actual": VERSION,
        "ultima": ultima,
        "hay_nueva": hay_nueva,
        "url_descarga": URL_DESCARGA,
    }
    if ultima is not None:
        with _lock:
            _cache["resultado"] = resultado
            _cache["expira"] = ahora + TTL_CACHE_SEGUNDOS
    return resultado


def limpiar_cache() -> None:
    """Solo para tests."""
    with _lock:
        _cache["resultado"] = None
        _cache["expira"] = 0.0
