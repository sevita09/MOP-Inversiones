"""Categorías propias de tickers (watchlists del usuario) y favoritos.

Los favoritos y las categorías viven en la base (no en localStorage) para
sobrevivir actualizaciones y compartirse entre el modo web y la app.
"""
from __future__ import annotations

import sqlite3
from typing import Optional


def listar(conexion: sqlite3.Connection) -> list[dict]:
    filas = conexion.execute("SELECT id, nombre FROM categorias ORDER BY nombre").fetchall()
    tickers = conexion.execute(
        "SELECT categoria_id, ticker FROM categorias_tickers ORDER BY ticker"
    ).fetchall()
    por_categoria: dict[int, list[str]] = {}
    for fila in tickers:
        por_categoria.setdefault(fila["categoria_id"], []).append(fila["ticker"])
    return [
        {"id": f["id"], "nombre": f["nombre"], "tickers": por_categoria.get(f["id"], [])}
        for f in filas
    ]


def crear(conexion: sqlite3.Connection, nombre: str) -> Optional[dict]:
    """Crea la categoría; None si ya existe una con ese nombre."""
    try:
        cursor = conexion.execute("INSERT INTO categorias (nombre) VALUES (?)", (nombre,))
    except sqlite3.IntegrityError:
        return None
    conexion.commit()
    return {"id": cursor.lastrowid, "nombre": nombre, "tickers": []}


def eliminar(conexion: sqlite3.Connection, id_categoria: int) -> bool:
    conexion.execute(
        "DELETE FROM categorias_tickers WHERE categoria_id = ?", (id_categoria,)
    )
    cursor = conexion.execute("DELETE FROM categorias WHERE id = ?", (id_categoria,))
    conexion.commit()
    return cursor.rowcount > 0


def agregar_ticker(conexion: sqlite3.Connection, id_categoria: int, ticker: str) -> bool:
    """False si la categoría no existe; idempotente si el ticker ya estaba."""
    existe = conexion.execute(
        "SELECT 1 FROM categorias WHERE id = ?", (id_categoria,)
    ).fetchone()
    if existe is None:
        return False
    conexion.execute(
        "INSERT OR IGNORE INTO categorias_tickers (categoria_id, ticker) VALUES (?, ?)",
        (id_categoria, ticker),
    )
    conexion.commit()
    return True


def quitar_ticker(conexion: sqlite3.Connection, id_categoria: int, ticker: str) -> bool:
    cursor = conexion.execute(
        "DELETE FROM categorias_tickers WHERE categoria_id = ? AND ticker = ?",
        (id_categoria, ticker),
    )
    conexion.commit()
    return cursor.rowcount > 0


# --- favoritos ---


def listar_favoritos(conexion: sqlite3.Connection) -> list[str]:
    filas = conexion.execute("SELECT ticker FROM favoritos ORDER BY rowid").fetchall()
    return [f["ticker"] for f in filas]


def reemplazar_favoritos(conexion: sqlite3.Connection, tickers: list[str]) -> None:
    """Guarda la lista completa (mismas semánticas que tenía localStorage)."""
    conexion.execute("DELETE FROM favoritos")
    conexion.executemany(
        "INSERT OR IGNORE INTO favoritos (ticker) VALUES (?)",
        [(t,) for t in tickers],
    )
    conexion.commit()
