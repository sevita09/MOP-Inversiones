from __future__ import annotations

import json
import sqlite3


def listar(conexion: sqlite3.Connection, ticker: str) -> list[dict]:
    filas = conexion.execute(
        "SELECT id, ticker, tipo, datos FROM dibujos WHERE ticker = ? ORDER BY id",
        (ticker,),
    ).fetchall()
    return [
        {"id": f["id"], "ticker": f["ticker"], "tipo": f["tipo"], "datos": json.loads(f["datos"])}
        for f in filas
    ]


def crear(conexion: sqlite3.Connection, ticker: str, tipo: str, datos: dict) -> dict:
    cursor = conexion.execute(
        "INSERT INTO dibujos (ticker, tipo, datos) VALUES (?, ?, ?)",
        (ticker, tipo, json.dumps(datos)),
    )
    conexion.commit()
    return {"id": cursor.lastrowid, "ticker": ticker, "tipo": tipo, "datos": datos}


def actualizar(conexion: sqlite3.Connection, id_dibujo: int, datos: dict) -> bool:
    cursor = conexion.execute(
        "UPDATE dibujos SET datos = ? WHERE id = ?",
        (json.dumps(datos), id_dibujo),
    )
    conexion.commit()
    return cursor.rowcount > 0


def eliminar(conexion: sqlite3.Connection, id_dibujo: int) -> bool:
    cursor = conexion.execute("DELETE FROM dibujos WHERE id = ?", (id_dibujo,))
    conexion.commit()
    return cursor.rowcount > 0
