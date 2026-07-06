"""Rutas de datos y de recursos, según corra en desarrollo o empaquetada.

Empaquetada (PyInstaller, `sys.frozen`): el bundle es de SOLO LECTURA, así que
lo que la app escribe —base `mop.db`, respaldos, logos— va a
`~/Library/Application Support/MOP`. Los recursos de solo lectura (el frontend
compilado) salen del bundle (`sys._MEIPASS`).

En desarrollo: todo cuelga de la raíz del repo, como siempre.
"""
from __future__ import annotations

import sys
from pathlib import Path

_RAIZ_REPO = Path(__file__).resolve().parents[2]


def empaquetada() -> bool:
    return bool(getattr(sys, "frozen", False))


def dir_datos() -> Path:
    """Carpeta donde la app escribe (base, respaldos, logos).

    El canal dev usa su propia carpeta: probar la app de desarrollo nunca
    toca los datos de la instalada.
    """
    if empaquetada():
        from app.canal import CANAL

        carpeta = "MOP Dev" if CANAL == "dev" else "MOP"
        destino = Path.home() / "Library" / "Application Support" / carpeta
        destino.mkdir(parents=True, exist_ok=True)
        return destino
    return _RAIZ_REPO


def dir_recursos() -> Path:
    """Carpeta de recursos de solo lectura incluidos en el bundle."""
    if empaquetada():
        return Path(getattr(sys, "_MEIPASS", _RAIZ_REPO))
    return _RAIZ_REPO
