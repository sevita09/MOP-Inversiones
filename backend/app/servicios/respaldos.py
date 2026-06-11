from __future__ import annotations

import shutil
from datetime import date
from pathlib import Path
from typing import Optional

from app.db import RUTA_BASE_DE_DATOS

CANTIDAD_A_CONSERVAR = 7


def respaldar_base(
    ruta_base: Path = RUTA_BASE_DE_DATOS,
    carpeta_respaldos: Optional[Path] = None,
    conservar: int = CANTIDAD_A_CONSERVAR,
) -> Optional[Path]:
    """Copia la base a backups/mop-AAAA-MM-DD.db y rota los respaldos viejos.

    Devuelve la ruta del respaldo creado, o None si no hay base todavía
    o si el respaldo de hoy ya existe (se respalda una vez por día).
    """
    ruta_base = Path(ruta_base)
    if not ruta_base.exists():
        return None

    carpeta = carpeta_respaldos or ruta_base.parent / "backups"
    carpeta.mkdir(exist_ok=True)

    destino = carpeta / f"mop-{date.today().isoformat()}.db"
    if destino.exists():
        return None

    shutil.copy2(ruta_base, destino)
    rotar_respaldos(carpeta, conservar)
    return destino


def rotar_respaldos(carpeta: Path, conservar: int = CANTIDAD_A_CONSERVAR) -> int:
    """Borra los respaldos más viejos dejando solo los últimos. Devuelve cuántos borró."""
    # El nombre mop-AAAA-MM-DD.db ordena alfabética = cronológicamente
    respaldos = sorted(carpeta.glob("mop-*.db"))
    a_borrar = respaldos[:-conservar] if conservar > 0 else respaldos
    for respaldo in a_borrar:
        respaldo.unlink()
    return len(a_borrar)
