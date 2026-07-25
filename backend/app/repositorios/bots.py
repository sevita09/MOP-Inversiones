"""Repositorio de bots: CRUD + duplicado sobre la tabla `bots`.

Los campos capital_json y reglas_json se guardan como TEXT y se exponen ya
parseados (dicts) hacia arriba: nadie fuera de este módulo maneja el JSON crudo.
"""
from __future__ import annotations

import json
import sqlite3
from typing import Optional

CAPITAL_DEFAULT = {"inicial": 1000000, "porcentaje_por_posicion": 100}
REGLAS_DEFAULT = {"version": 1, "entrada": [], "salida": [], "filtros": []}
RIESGO_DEFAULT = {
    "stop_loss_pct": None,
    "stop_atr_mult": None,
    "take_profit_pct": None,
    "salida_ema_central": False,
    "trailing_pct": None,
    "atr_periodo": 14,
    "sizing_riesgo_pct": None,
}


def _a_dict(fila: sqlite3.Row) -> dict:
    bot = dict(fila)
    bot["capital"] = json.loads(bot.pop("capital_json"))
    bot["reglas"] = json.loads(bot.pop("reglas_json"))
    crudo_riesgo = bot.pop("riesgo_json", None)
    bot["riesgo"] = json.loads(crudo_riesgo) if crudo_riesgo else dict(RIESGO_DEFAULT)
    # Resumen del último backtest (caché); None si nunca se backtesteó
    crudo = bot.pop("metricas_json", None)
    bot["metricas"] = json.loads(crudo) if crudo else None
    bot["activo"] = bool(bot["activo"])
    return bot


def guardar_metricas(conexion: sqlite3.Connection, id_bot: int, resumen: dict) -> None:
    """Cachea el resumen del último backtest en el bot (para la lista de bots)."""
    conexion.execute(
        "UPDATE bots SET metricas_json = ? WHERE id = ?", (json.dumps(resumen), id_bot)
    )
    conexion.commit()


def crear(
    conexion: sqlite3.Connection,
    nombre: str,
    ticker: str,
    temporalidad: str,
    moneda: str = "ARS",
    capital: Optional[dict] = None,
    reglas: Optional[dict] = None,
    riesgo: Optional[dict] = None,
    activo: bool = True,
) -> Optional[dict]:
    """Crea el bot; None si ya existe uno con ese nombre."""
    try:
        cursor = conexion.execute(
            """INSERT INTO bots (nombre, ticker, temporalidad, moneda, capital_json,
                                 reglas_json, riesgo_json, activo)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                nombre,
                ticker,
                temporalidad,
                moneda,
                json.dumps(capital or CAPITAL_DEFAULT),
                json.dumps(reglas or REGLAS_DEFAULT),
                json.dumps(riesgo or RIESGO_DEFAULT),
                int(activo),
            ),
        )
    except sqlite3.IntegrityError:
        return None
    conexion.commit()
    return obtener(conexion, cursor.lastrowid)


def listar(conexion: sqlite3.Connection) -> list[dict]:
    filas = conexion.execute("SELECT * FROM bots ORDER BY nombre").fetchall()
    return [_a_dict(f) for f in filas]


def obtener(conexion: sqlite3.Connection, id_bot: int) -> Optional[dict]:
    fila = conexion.execute("SELECT * FROM bots WHERE id = ?", (id_bot,)).fetchone()
    return _a_dict(fila) if fila else None


def actualizar(conexion: sqlite3.Connection, id_bot: int, cambios: dict) -> Optional[dict]:
    """Actualiza los campos presentes en `cambios`; None si el nombre choca.

    Devuelve el bot actualizado, o False si no existe.
    """
    actual = obtener(conexion, id_bot)
    if actual is None:
        return False
    columnas, valores = [], []
    for campo in ("nombre", "ticker", "temporalidad", "moneda"):
        if campo in cambios:
            columnas.append(f"{campo} = ?")
            valores.append(cambios[campo])
    for campo, columna in (
        ("capital", "capital_json"),
        ("reglas", "reglas_json"),
        ("riesgo", "riesgo_json"),
    ):
        if campo in cambios:
            columnas.append(f"{columna} = ?")
            valores.append(json.dumps(cambios[campo]))
    if "activo" in cambios:
        columnas.append("activo = ?")
        valores.append(int(cambios["activo"]))
    if not columnas:
        return actual
    columnas.append("actualizado = datetime('now')")
    try:
        conexion.execute(
            f"UPDATE bots SET {', '.join(columnas)} WHERE id = ?", (*valores, id_bot)
        )
    except sqlite3.IntegrityError:
        return None
    conexion.commit()
    return obtener(conexion, id_bot)


def eliminar(conexion: sqlite3.Connection, id_bot: int) -> bool:
    cursor = conexion.execute("DELETE FROM bots WHERE id = ?", (id_bot,))
    conexion.commit()
    return cursor.rowcount > 0


def duplicar(conexion: sqlite3.Connection, id_bot: int) -> Optional[dict]:
    """Copia el bot como '<nombre> (copia)'; numera si ya hay copias."""
    original = obtener(conexion, id_bot)
    if original is None:
        return None
    nombre = f"{original['nombre']} (copia)"
    numero = 2
    while _existe_nombre(conexion, nombre):
        nombre = f"{original['nombre']} (copia {numero})"
        numero += 1
    return crear(
        conexion,
        nombre,
        original["ticker"],
        original["temporalidad"],
        original["moneda"],
        original["capital"],
        original["reglas"],
        original["riesgo"],
        original["activo"],
    )


def _existe_nombre(conexion: sqlite3.Connection, nombre: str) -> bool:
    return (
        conexion.execute("SELECT 1 FROM bots WHERE nombre = ?", (nombre,)).fetchone()
        is not None
    )
