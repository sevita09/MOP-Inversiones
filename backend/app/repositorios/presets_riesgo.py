"""Presets de gestión de riesgo: configuraciones guardadas para reusar en bots.

Expone el riesgo ya parseado (dict); el JSON crudo no sale de este módulo.
"""
from __future__ import annotations

import json
import sqlite3
from typing import Optional


def _a_dict(fila: sqlite3.Row) -> dict:
    preset = dict(fila)
    preset["riesgo"] = json.loads(preset.pop("riesgo_json"))
    return preset


def listar(conexion: sqlite3.Connection) -> list[dict]:
    filas = conexion.execute("SELECT * FROM presets_riesgo ORDER BY nombre").fetchall()
    return [_a_dict(f) for f in filas]


def obtener(conexion: sqlite3.Connection, id_preset: int) -> Optional[dict]:
    fila = conexion.execute(
        "SELECT * FROM presets_riesgo WHERE id = ?", (id_preset,)
    ).fetchone()
    return _a_dict(fila) if fila else None


def crear(conexion: sqlite3.Connection, nombre: str, riesgo: dict) -> Optional[dict]:
    """Crea el preset; None si ya existe uno con ese nombre."""
    try:
        cursor = conexion.execute(
            "INSERT INTO presets_riesgo (nombre, riesgo_json) VALUES (?, ?)",
            (nombre, json.dumps(riesgo)),
        )
    except sqlite3.IntegrityError:
        return None
    conexion.commit()
    return obtener(conexion, cursor.lastrowid)


def eliminar(conexion: sqlite3.Connection, id_preset: int) -> bool:
    cursor = conexion.execute("DELETE FROM presets_riesgo WHERE id = ?", (id_preset,))
    conexion.commit()
    return cursor.rowcount > 0
