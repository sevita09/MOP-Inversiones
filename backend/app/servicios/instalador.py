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


def extraer_app_del_dmg(ruta_dmg: Path, armado: Path) -> Path:
    """Monta el dmg, copia el .app a la carpeta de armado y desmonta."""
    punto = Path(tempfile.mkdtemp(prefix="mop-dmg-"))
    subprocess.run(
        ["hdiutil", "attach", str(ruta_dmg), "-nobrowse", "-mountpoint", str(punto)],
        check=True, capture_output=True,
    )
    try:
        # ditto conserva permisos, atributos y la firma del bundle
        subprocess.run(
            ["ditto", str(punto / NOMBRE_APP), str(armado / NOMBRE_APP)],
            check=True, capture_output=True,
        )
    finally:
        subprocess.run(["hdiutil", "detach", str(punto)], capture_output=True)
    return armado / NOMBRE_APP


def escribir_ayudante(carpeta: Path, pid: int, armado: Path) -> Path:
    """Script que espera el cierre de la app, la reemplaza y la relanza."""
    ruta = carpeta / "actualizar_mop.sh"
    ruta.write_text(f"""#!/bin/bash
# Ayudante de actualización de MOP: corre desacoplado de la app.
while kill -0 {pid} 2>/dev/null; do sleep 0.5; done   # esperar el cierre real
rm -rf "{RUTA_APP_INSTALADA}"
ditto "{armado / NOMBRE_APP}" "{RUTA_APP_INSTALADA}"
rm -rf "{armado}"
open "{RUTA_APP_INSTALADA}"
rm -f "{ruta}"
""")
    ruta.chmod(0o755)
    return ruta


def _cerrar_app_en(segundos: float) -> None:
    """Cierra la app: destruye la ventana (el proceso muere con ella)."""
    def cerrar():
        try:
            import webview

            for ventana in webview.windows:
                ventana.destroy()
        except Exception:
            pass
        # Red de seguridad: si no había ventana, terminar igual
        threading.Timer(2.0, lambda: os._exit(0)).start()

    threading.Timer(segundos, cerrar).start()


def instalar_actualizacion(cliente: Optional[httpx.Client] = None) -> dict:
    """Descarga la última release, prepara el reemplazo y cierra la app.

    Devuelve la versión que se está instalando. Lanza ValueError si no hay
    nada instalable (sin release nueva o sin asset .dmg).
    """
    release = release_instalable(cliente)
    if release is None:
        raise ValueError("No hay una versión nueva instalable")

    trabajo = Path(tempfile.mkdtemp(prefix="mop-actualizacion-"))
    ruta_dmg = descargar_dmg(release["url"], trabajo / release["nombre"], cliente)
    extraer_app_del_dmg(ruta_dmg, trabajo)
    ruta_dmg.unlink()  # el dmg ya no hace falta; el .app quedó en la carpeta

    ayudante = escribir_ayudante(trabajo, os.getpid(), trabajo)
    # start_new_session: el ayudante queda huérfano a propósito y sobrevive al cierre
    subprocess.Popen(["/bin/bash", str(ayudante)], start_new_session=True)

    _cerrar_app_en(1.0)  # dar tiempo a que la respuesta HTTP llegue al frontend
    return {"instalando": release["version"]}
