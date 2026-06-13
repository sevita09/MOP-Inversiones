from __future__ import annotations

import sqlite3
from typing import Optional


def obtener_ultima_sync(
    conexion: sqlite3.Connection, ticker: str, temporalidad: str
) -> Optional[str]:
    """Devuelve el momento (ISO UTC) de la última sincronización, o None."""
    fila = conexion.execute(
        "SELECT ultima_sync FROM registro_sync WHERE ticker = ? AND temporalidad = ?",
        (ticker, temporalidad),
    ).fetchone()
    return fila["ultima_sync"] if fila else None


def registrar_sync(
    conexion: sqlite3.Connection, ticker: str, temporalidad: str, momento: str
) -> None:
    conexion.execute(
        """
        INSERT OR REPLACE INTO registro_sync (ticker, temporalidad, ultima_sync)
        VALUES (?, ?, ?)
        """,
        (ticker, temporalidad, momento),
    )
    conexion.commit()
