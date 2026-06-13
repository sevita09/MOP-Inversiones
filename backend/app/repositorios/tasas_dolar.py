from __future__ import annotations

import sqlite3
from bisect import bisect_right
from typing import Iterable, Optional

CCL = "CCL"
OFICIAL = "OFICIAL"


def guardar_tasas(conexion: sqlite3.Connection, tasas: Iterable[dict]) -> int:
    """Inserta o reemplaza tasas. Cada tasa: {fecha, tipo, valor}."""
    filas = [(t["fecha"], t["tipo"], t["valor"]) for t in tasas]
    conexion.executemany(
        "INSERT OR REPLACE INTO tasas_dolar (fecha, tipo, valor) VALUES (?, ?, ?)",
        filas,
    )
    conexion.commit()
    return len(filas)


def obtener_tasas(
    conexion: sqlite3.Connection, tipo: str = CCL
) -> list[dict]:
    """Todas las tasas de un tipo, ordenadas por fecha ascendente."""
    filas = conexion.execute(
        "SELECT fecha, tipo, valor FROM tasas_dolar WHERE tipo = ? ORDER BY fecha",
        (tipo,),
    ).fetchall()
    return [dict(fila) for fila in filas]


def obtener_tasa_en_fecha(
    conexion: sqlite3.Connection, fecha: str, tipo: str = CCL
) -> Optional[float]:
    """Tasa vigente en una fecha: la de ese día o la del día hábil anterior.

    Usa búsqueda binaria sobre las fechas ordenadas. Devuelve None si la fecha
    es anterior a la primera tasa conocida.
    """
    fechas = [t["fecha"] for t in obtener_tasas(conexion, tipo)]
    if not fechas:
        return None
    posicion = bisect_right(fechas, fecha)
    if posicion == 0:
        return None
    fecha_vigente = fechas[posicion - 1]
    fila = conexion.execute(
        "SELECT valor FROM tasas_dolar WHERE fecha = ? AND tipo = ?",
        (fecha_vigente, tipo),
    ).fetchone()
    return fila["valor"] if fila else None
