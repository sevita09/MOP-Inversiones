"""Señales de bots: persistencia de los disparos y el estado 'sin ver'.

Única por (bot_id, ts_barra, lado): guardar es idempotente (INSERT OR IGNORE),
así el sync que corre cada 15 min no duplica la señal de la misma barra.
"""
from __future__ import annotations

import json
import sqlite3


def _a_dict(fila: sqlite3.Row) -> dict:
    senal = dict(fila)
    senal["detalle"] = json.loads(senal.pop("detalle_json"))
    senal["vista"] = bool(senal["vista"])
    return senal


def guardar(
    conexion: sqlite3.Connection,
    bot_id: int,
    ticker: str,
    ts_barra: int,
    lado: str,
    detalle: dict,
) -> bool:
    """True si la señal es nueva; False si ya existía (misma barra, mismo lado)."""
    cursor = conexion.execute(
        """INSERT OR IGNORE INTO senales (bot_id, ticker, ts_barra, lado, detalle_json)
           VALUES (?, ?, ?, ?, ?)""",
        (bot_id, ticker, ts_barra, lado, json.dumps(detalle)),
    )
    conexion.commit()
    return cursor.rowcount > 0


def registrar(
    conexion: sqlite3.Connection,
    bot_id: int,
    ticker: str,
    ts_barra: int,
    lado: str,
    detalle: dict,
) -> str:
    """Una sola tarjeta por (bot, lado): no acumula señales del mismo bot.

    - 'nueva': no existía → se inserta.
    - 'actualizada': existía en OTRA barra → se refresca con los datos de ahora
      (nueva barra + desglose) y vuelve a marcarse sin ver (avisa de nuevo).
    - 'sin_cambios': existía en la MISMA barra → no se toca (no re-avisa cada
      15 min ni pisa el estado 'vista').

    Si por señales viejas hubiera más de una fila del mismo bot+lado, colapsa a
    una (se queda con la de la barra más nueva y borra el resto).
    """
    filas = conexion.execute(
        "SELECT id, ts_barra FROM senales WHERE bot_id = ? AND lado = ? ORDER BY ts_barra DESC",
        (bot_id, lado),
    ).fetchall()

    if not filas:
        conexion.execute(
            """INSERT INTO senales (bot_id, ticker, ts_barra, lado, detalle_json)
               VALUES (?, ?, ?, ?, ?)""",
            (bot_id, ticker, ts_barra, lado, json.dumps(detalle)),
        )
        conexion.commit()
        return "nueva"

    principal = filas[0]
    sobrantes = [f["id"] for f in filas[1:]]
    if sobrantes:
        eliminar_varias(conexion, sobrantes)

    if principal["ts_barra"] == ts_barra:
        conexion.commit()
        return "sin_cambios"

    conexion.execute(
        """UPDATE senales
           SET ticker = ?, ts_barra = ?, detalle_json = ?, vista = 0,
               creado = datetime('now')
           WHERE id = ?""",
        (ticker, ts_barra, json.dumps(detalle), principal["id"]),
    )
    conexion.commit()
    return "actualizada"


def listar(conexion: sqlite3.Connection, limite: int = 200) -> list[dict]:
    filas = conexion.execute(
        "SELECT * FROM senales ORDER BY ts_barra DESC, id DESC LIMIT ?", (limite,)
    ).fetchall()
    return [_a_dict(f) for f in filas]


def contar_sin_ver(conexion: sqlite3.Connection) -> int:
    fila = conexion.execute("SELECT COUNT(*) AS n FROM senales WHERE vista = 0").fetchone()
    return fila["n"]


def marcar_todas_vistas(conexion: sqlite3.Connection) -> int:
    cursor = conexion.execute("UPDATE senales SET vista = 1 WHERE vista = 0")
    conexion.commit()
    return cursor.rowcount


def eliminar(conexion: sqlite3.Connection, id_senal: int) -> bool:
    cursor = conexion.execute("DELETE FROM senales WHERE id = ?", (id_senal,))
    conexion.commit()
    return cursor.rowcount > 0


def eliminar_varias(conexion: sqlite3.Connection, ids: list[int]) -> int:
    if not ids:
        return 0
    marcadores = ",".join("?" * len(ids))
    cursor = conexion.execute(f"DELETE FROM senales WHERE id IN ({marcadores})", ids)
    conexion.commit()
    return cursor.rowcount


def borrar_de_bot(conexion: sqlite3.Connection, bot_id: int) -> None:
    """Al borrar un bot, sus señales se van con él (no hay FK declarada)."""
    conexion.execute("DELETE FROM senales WHERE bot_id = ?", (bot_id,))
    conexion.commit()
