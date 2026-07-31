"""Retornos logarítmicos precalculados, por ticker y temporalidad.

Se consultan de dos maneras: la serie de un papel (estacionalidad) y todos los
papeles de una fecha alineados (correlaciones). El índice
`(temporalidad, moneda, ts)` está para la segunda.
"""
from __future__ import annotations

import sqlite3
from typing import Iterable, Optional


def guardar(conexion: sqlite3.Connection, retornos: Iterable[dict]) -> int:
    """Inserta o reemplaza retornos. Cada uno: {ticker, temporalidad, moneda, ts, retorno}."""
    filas = [
        (r["ticker"], r["temporalidad"], r["moneda"], r["ts"], r["retorno"]) for r in retornos
    ]
    if not filas:
        return 0
    conexion.executemany(
        """INSERT OR REPLACE INTO retornos (ticker, temporalidad, moneda, ts, retorno)
           VALUES (?, ?, ?, ?, ?)""",
        filas,
    )
    conexion.commit()
    return len(filas)


def obtener(
    conexion: sqlite3.Connection,
    ticker: str,
    temporalidad: str,
    moneda: str = "ARS",
    desde: Optional[int] = None,
) -> list[dict]:
    """Serie de retornos de un papel, ordenada por fecha."""
    consulta = """SELECT ts, retorno FROM retornos
                  WHERE ticker = ? AND temporalidad = ? AND moneda = ?"""
    parametros: list = [ticker, temporalidad, moneda]
    if desde is not None:
        consulta += " AND ts >= ?"
        parametros.append(desde)
    consulta += " ORDER BY ts"
    return [dict(fila) for fila in conexion.execute(consulta, parametros)]


def ultimo_ts(
    conexion: sqlite3.Connection, ticker: str, temporalidad: str, moneda: str
) -> Optional[int]:
    """El ts del retorno más nuevo guardado, para seguir desde ahí."""
    fila = conexion.execute(
        """SELECT MAX(ts) AS ts FROM retornos
           WHERE ticker = ? AND temporalidad = ? AND moneda = ?""",
        (ticker, temporalidad, moneda),
    ).fetchone()
    return fila["ts"] if fila and fila["ts"] is not None else None


def alineados(
    conexion: sqlite3.Connection,
    tickers: list[str],
    temporalidad: str,
    moneda: str = "ARS",
    desde: Optional[int] = None,
) -> dict[int, dict[str, float]]:
    """Retornos de varios papeles indexados por fecha: `{ts: {ticker: retorno}}`.

    Es la forma que necesitan las correlaciones: en cada fecha, qué hizo cada
    papel. Las fechas donde un papel no operó simplemente no lo incluyen, así
    quien consume decide si descarta la fecha o la usa igual.
    """
    if not tickers:
        return {}
    marcadores = ",".join("?" * len(tickers))
    consulta = f"""SELECT ts, ticker, retorno FROM retornos
                   WHERE temporalidad = ? AND moneda = ? AND ticker IN ({marcadores})"""
    parametros: list = [temporalidad, moneda, *tickers]
    if desde is not None:
        consulta += " AND ts >= ?"
        parametros.append(desde)
    consulta += " ORDER BY ts"

    matriz: dict[int, dict[str, float]] = {}
    for fila in conexion.execute(consulta, parametros):
        matriz.setdefault(fila["ts"], {})[fila["ticker"]] = fila["retorno"]
    return matriz


def contar(conexion: sqlite3.Connection) -> int:
    return conexion.execute("SELECT COUNT(*) AS n FROM retornos").fetchone()["n"]


def borrar_ticker(conexion: sqlite3.Connection, ticker: str) -> int:
    cursor = conexion.execute("DELETE FROM retornos WHERE ticker = ?", (ticker,))
    conexion.commit()
    return cursor.rowcount
