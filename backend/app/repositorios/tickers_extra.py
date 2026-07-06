"""Tickers agregados por el usuario (fuera del universo fijo de config.py)."""
from __future__ import annotations

import sqlite3


def listar(conexion: sqlite3.Connection) -> list[dict]:
    filas = conexion.execute(
        "SELECT ticker, simbolo_yf, grupo FROM tickers_extra ORDER BY ticker"
    ).fetchall()
    return [
        {"ticker": f["ticker"], "simbolo_yf": f["simbolo_yf"], "grupo": f["grupo"]}
        for f in filas
    ]


def por_grupo(conexion: sqlite3.Connection, grupo: str) -> list[str]:
    filas = conexion.execute(
        "SELECT ticker FROM tickers_extra WHERE grupo = ? ORDER BY ticker", (grupo,)
    ).fetchall()
    return [f["ticker"] for f in filas]


def agregar(
    conexion: sqlite3.Connection, ticker: str, simbolo_yf: str, grupo: str
) -> bool:
    """False si el ticker ya estaba agregado."""
    try:
        conexion.execute(
            "INSERT INTO tickers_extra (ticker, simbolo_yf, grupo) VALUES (?, ?, ?)",
            (ticker, simbolo_yf, grupo),
        )
    except sqlite3.IntegrityError:
        return False
    conexion.commit()
    return True


def eliminar(conexion: sqlite3.Connection, ticker: str) -> bool:
    cursor = conexion.execute("DELETE FROM tickers_extra WHERE ticker = ?", (ticker,))
    conexion.commit()
    return cursor.rowcount > 0


def simbolo_de(conexion: sqlite3.Connection, ticker: str) -> str | None:
    fila = conexion.execute(
        "SELECT simbolo_yf FROM tickers_extra WHERE ticker = ?", (ticker,)
    ).fetchone()
    return fila["simbolo_yf"] if fila else None
