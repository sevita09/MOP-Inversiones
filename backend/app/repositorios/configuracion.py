"""Preferencias del usuario en clave/valor.

Se guardan como TEXT y se leen con su tipo (`leer_numero`), así sumar una
preferencia nueva no necesita migrar la tabla.
"""
from __future__ import annotations

import sqlite3
from typing import Optional


def leer(conexion: sqlite3.Connection, clave: str) -> Optional[str]:
    fila = conexion.execute(
        "SELECT valor FROM configuracion WHERE clave = ?", (clave,)
    ).fetchone()
    return fila["valor"] if fila else None


def leer_numero(conexion: sqlite3.Connection, clave: str, default: float) -> float:
    valor = leer(conexion, clave)
    if valor is None:
        return default
    try:
        return float(valor)
    except ValueError:
        return default


def guardar(conexion: sqlite3.Connection, clave: str, valor) -> None:
    conexion.execute(
        "INSERT OR REPLACE INTO configuracion (clave, valor) VALUES (?, ?)",
        (clave, str(valor)),
    )
    conexion.commit()
