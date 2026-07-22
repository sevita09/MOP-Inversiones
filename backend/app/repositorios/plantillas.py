"""Plantillas de estrategia creadas por el usuario (persistidas en la base).

Las 4 plantillas de la metodología viven fijas en `servicios/bots/plantillas.py`.
Estas son las que el usuario guarda desde el editor para no depender de que
agreguemos nuevas: se listan junto a las predefinidas. Expone las reglas ya
parseadas (dict); el JSON crudo no sale de este módulo.
"""
from __future__ import annotations

import json
import sqlite3
from typing import Optional


def _a_dict(fila: sqlite3.Row) -> dict:
    plantilla = dict(fila)
    plantilla["reglas"] = json.loads(plantilla.pop("reglas_json"))
    return plantilla


def listar(conexion: sqlite3.Connection) -> list[dict]:
    filas = conexion.execute("SELECT * FROM plantillas ORDER BY nombre").fetchall()
    return [_a_dict(f) for f in filas]


def obtener(conexion: sqlite3.Connection, id_plantilla: int) -> Optional[dict]:
    fila = conexion.execute(
        "SELECT * FROM plantillas WHERE id = ?", (id_plantilla,)
    ).fetchone()
    return _a_dict(fila) if fila else None


def crear(
    conexion: sqlite3.Connection,
    nombre: str,
    descripcion: str,
    temporalidad: str,
    moneda: str,
    reglas: dict,
) -> Optional[dict]:
    """Crea la plantilla; None si ya existe una con ese nombre."""
    try:
        cursor = conexion.execute(
            """INSERT INTO plantillas (nombre, descripcion, temporalidad, moneda, reglas_json)
               VALUES (?, ?, ?, ?, ?)""",
            (nombre, descripcion, temporalidad, moneda, json.dumps(reglas)),
        )
    except sqlite3.IntegrityError:
        return None
    conexion.commit()
    return obtener(conexion, cursor.lastrowid)


def eliminar(conexion: sqlite3.Connection, id_plantilla: int) -> bool:
    cursor = conexion.execute("DELETE FROM plantillas WHERE id = ?", (id_plantilla,))
    conexion.commit()
    return cursor.rowcount > 0
