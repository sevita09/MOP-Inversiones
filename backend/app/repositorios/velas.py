from __future__ import annotations

import sqlite3
from typing import Iterable, Optional


def guardar_velas(conexion: sqlite3.Connection, velas: Iterable[dict]) -> int:
    """Inserta o reemplaza velas. Devuelve cuántas se guardaron."""
    filas = [
        (
            vela["ticker"],
            vela["temporalidad"],
            vela["ts"],
            vela["apertura"],
            vela["maximo"],
            vela["minimo"],
            vela["cierre"],
            vela.get("volumen", 0.0),
            vela.get("es_faltante", 0),
        )
        for vela in velas
    ]
    conexion.executemany(
        """
        INSERT OR REPLACE INTO velas
        (ticker, temporalidad, ts, apertura, maximo, minimo, cierre, volumen, es_faltante)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        filas,
    )
    conexion.commit()
    return len(filas)


def obtener_ultimo_ts(
    conexion: sqlite3.Connection, ticker: str, temporalidad: str
) -> Optional[int]:
    """Timestamp de la vela más reciente guardada, o None si no hay ninguna."""
    fila = conexion.execute(
        "SELECT MAX(ts) AS ultimo FROM velas WHERE ticker = ? AND temporalidad = ?",
        (ticker, temporalidad),
    ).fetchone()
    return fila["ultimo"]


def obtener_ultima_vela(
    conexion: sqlite3.Connection, ticker: str, temporalidad: str
) -> Optional[dict]:
    """La vela más reciente completa, o None si no hay ninguna."""
    fila = conexion.execute(
        "SELECT * FROM velas WHERE ticker = ? AND temporalidad = ? ORDER BY ts DESC LIMIT 1",
        (ticker, temporalidad),
    ).fetchone()
    return dict(fila) if fila else None


def obtener_velas(
    conexion: sqlite3.Connection,
    ticker: str,
    temporalidad: str,
    desde: Optional[int] = None,
    hasta: Optional[int] = None,
) -> list[dict]:
    """Devuelve las velas del ticker/temporalidad ordenadas por ts ascendente."""
    consulta = "SELECT * FROM velas WHERE ticker = ? AND temporalidad = ?"
    parametros: list = [ticker, temporalidad]
    if desde is not None:
        consulta += " AND ts >= ?"
        parametros.append(desde)
    if hasta is not None:
        consulta += " AND ts <= ?"
        parametros.append(hasta)
    consulta += " ORDER BY ts"
    return [dict(fila) for fila in conexion.execute(consulta, parametros)]
