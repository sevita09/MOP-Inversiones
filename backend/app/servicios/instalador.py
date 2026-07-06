"""Auto-instalación de actualizaciones.

Flujo completo cuando el usuario acepta instalar:
1. Se consulta la última release de GitHub y se elige su asset `.dmg`.
2. Se descarga a una carpeta temporal y se monta con `hdiutil`.
3. El `.app` nuevo se copia a una carpeta de armado y se desmonta el dmg.
4. Se lanza un script ayudante desacoplado del proceso (sobrevive al cierre):
   espera a que la app se cierre, reemplaza el `.app` en /Applications,
   limpia y relanza. Una app no puede pisarse a sí misma mientras corre —
   por eso el reemplazo ocurre recién después del cierre.
5. La app se cierra sola (la ventana se destruye y el proceso termina).

Solo corre empaquetada: en desarrollo no hay `.app` que reemplazar.
"""
from __future__ import annotations

import os
import subprocess
import tempfile
import threading
from pathlib import Path
from typing import Optional

import httpx

from app.servicios.actualizacion import REPO_GITHUB, parsear_version
from app.version import VERSION

URL_ULTIMA_RELEASE = f"https://api.github.com/repos/{REPO_GITHUB}/releases/latest"
RUTA_APP_INSTALADA = "/Applications/MOP - Inversiones.app"
NOMBRE_APP = "MOP - Inversiones.app"


def asset_dmg(release: dict) -> Optional[dict]:
    """El asset .dmg de una release de GitHub, o None si no tiene."""
    for asset in release.get("assets", []):
        if asset.get("name", "").endswith(".dmg"):
            return asset
    return None


def release_instalable(cliente: Optional[httpx.Client] = None) -> Optional[dict]:
    """Última release si es más nueva que la versión corriendo y trae un .dmg.

    Devuelve {"version": "X.Y.Z", "url": url_del_dmg, "nombre": archivo} o None.
    """
    try:
        propio = cliente or httpx.Client(timeout=10)
        try:
            respuesta = propio.get(URL_ULTIMA_RELEASE)
            respuesta.raise_for_status()
            release = respuesta.json()
        finally:
            if cliente is None:
                propio.close()
    except Exception:
        return None

    numeros = parsear_version(release.get("tag_name", ""))
    if numeros is None or numeros <= parsear_version(VERSION):
        return None
    dmg = asset_dmg(release)
    if dmg is None:
        return None
    return {
        "version": ".".join(str(n) for n in numeros),
        "url": dmg["browser_download_url"],
        "nombre": dmg["name"],
    }


def descargar_dmg(url: str, destino: Path, cliente: Optional[httpx.Client] = None) -> Path:
    """Descarga el .dmg por streaming (los assets de GitHub redirigen a un CDN)."""
    propio = cliente or httpx.Client(timeout=60, follow_redirects=True)
    try:
        with propio.stream("GET", url) as respuesta:
            respuesta.raise_for_status()
            with open(destino, "wb") as archivo:
                for parte in respuesta.iter_bytes():
                    archivo.write(parte)
    finally:
        if cliente is None:
            propio.close()
    return destino
