"""Splits de acciones: los eventos que multiplican los papeles sin mover plata."""
from __future__ import annotations

import sqlite3
from typing import Optional


def crear(
    conexion: sqlite3.Connection, ticker: str, fecha: str, ratio: float, nota: str = ""
) -> Optional[dict]:
    """Crea el split; None si ya hay uno de ese papel en esa fecha."""
    try:
        cursor = conexion.execute(
            "INSERT INTO splits (ticker, fecha, ratio, nota) VALUES (?, ?, ?, ?)",
            (ticker, fecha, ratio, nota),
        )
    except sqlite3.IntegrityError:
        return None
    conexion.commit()
    return obtener(conexion, cursor.lastrowid)


def obtener(conexion: sqlite3.Connection, id_split: int) -> Optional[dict]:
    fila = conexion.execute("SELECT * FROM splits WHERE id = ?", (id_split,)).fetchone()
    return dict(fila) if fila else None


def listar(conexion: sqlite3.Connection, ticker: Optional[str] = None) -> list[dict]:
    consulta = "SELECT * FROM splits"
    parametros: list = []
    if ticker:
        consulta += " WHERE ticker = ?"
        parametros.append(ticker)
    consulta += " ORDER BY fecha DESC, id DESC"
    return [dict(fila) for fila in conexion.execute(consulta, parametros)]


def listar_cronologicos(conexion: sqlite3.Connection, ticker: str) -> list[dict]:
    """Orden ascendente: el que necesita el recorrido de lotes del FIFO."""
    filas = conexion.execute(
        "SELECT * FROM splits WHERE ticker = ? ORDER BY fecha, id", (ticker,)
    ).fetchall()
    return [dict(fila) for fila in filas]


def eliminar(conexion: sqlite3.Connection, id_split: int) -> bool:
    cursor = conexion.execute("DELETE FROM splits WHERE id = ?", (id_split,))
    conexion.commit()
    return cursor.rowcount > 0
