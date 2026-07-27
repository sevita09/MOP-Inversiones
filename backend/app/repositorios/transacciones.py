"""Operaciones reales de la cartera: compras y ventas cargadas por el usuario.

Ordenadas por fecha (y por id dentro del mismo día) porque el FIFO de las
tenencias (v6.2) depende de ese orden: la primera compra es la primera que se
consume al vender.
"""
from __future__ import annotations

import sqlite3
from typing import Optional

CAMPOS = ("ticker", "tipo", "fecha", "cantidad", "precio", "comision", "nota")


def crear(
    conexion: sqlite3.Connection,
    ticker: str,
    tipo: str,
    fecha: str,
    cantidad: float,
    precio: float,
    comision: float = 0,
    nota: str = "",
) -> dict:
    cursor = conexion.execute(
        """INSERT INTO transacciones (ticker, tipo, fecha, cantidad, precio, comision, nota)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (ticker, tipo, fecha, cantidad, precio, comision, nota),
    )
    conexion.commit()
    return obtener(conexion, cursor.lastrowid)


def listar(conexion: sqlite3.Connection, ticker: Optional[str] = None) -> list[dict]:
    """Todas las operaciones, más nuevas primero (para el historial en pantalla)."""
    consulta = "SELECT * FROM transacciones"
    parametros: list = []
    if ticker:
        consulta += " WHERE ticker = ?"
        parametros.append(ticker)
    consulta += " ORDER BY fecha DESC, id DESC"
    return [dict(fila) for fila in conexion.execute(consulta, parametros)]


def listar_cronologicas(conexion: sqlite3.Connection, ticker: Optional[str] = None) -> list[dict]:
    """Orden cronológico ascendente: el que necesita el FIFO de tenencias."""
    consulta = "SELECT * FROM transacciones"
    parametros: list = []
    if ticker:
        consulta += " WHERE ticker = ?"
        parametros.append(ticker)
    consulta += " ORDER BY fecha, id"
    return [dict(fila) for fila in conexion.execute(consulta, parametros)]


def obtener(conexion: sqlite3.Connection, id_transaccion: int) -> Optional[dict]:
    fila = conexion.execute(
        "SELECT * FROM transacciones WHERE id = ?", (id_transaccion,)
    ).fetchone()
    return dict(fila) if fila else None


def actualizar(conexion: sqlite3.Connection, id_transaccion: int, cambios: dict) -> Optional[dict]:
    """Actualiza los campos presentes; None si la transacción no existe."""
    if obtener(conexion, id_transaccion) is None:
        return None
    columnas = [f"{campo} = ?" for campo in CAMPOS if campo in cambios]
    valores = [cambios[campo] for campo in CAMPOS if campo in cambios]
    if not columnas:
        return obtener(conexion, id_transaccion)
    conexion.execute(
        f"UPDATE transacciones SET {', '.join(columnas)} WHERE id = ?",
        (*valores, id_transaccion),
    )
    conexion.commit()
    return obtener(conexion, id_transaccion)


def eliminar(conexion: sqlite3.Connection, id_transaccion: int) -> bool:
    cursor = conexion.execute("DELETE FROM transacciones WHERE id = ?", (id_transaccion,))
    conexion.commit()
    return cursor.rowcount > 0


def tickers_operados(conexion: sqlite3.Connection) -> list[str]:
    """Papeles con al menos una operación (para armar la cartera)."""
    filas = conexion.execute(
        "SELECT DISTINCT ticker FROM transacciones ORDER BY ticker"
    ).fetchall()
    return [fila["ticker"] for fila in filas]


def cantidades_en_cartera(conexion: sqlite3.Connection) -> dict:
    """Papeles que se tienen hoy por ticker: compras menos ventas.

    Solo los que quedan en positivo — es lo que se puede vender. El detalle con
    precio promedio y P&L llega en v6.2; acá alcanza con la cantidad.
    """
    # El HAVING repite la expresión a propósito: el alias `cantidad` chocaría con
    # la columna del mismo nombre y SQLite filtraría por la columna, no por la suma
    filas = conexion.execute(
        """SELECT ticker,
                  SUM(CASE WHEN tipo = 'compra' THEN cantidad ELSE -cantidad END) AS en_cartera
           FROM transacciones
           GROUP BY ticker
           HAVING SUM(CASE WHEN tipo = 'compra' THEN cantidad ELSE -cantidad END) > 0
           ORDER BY ticker"""
    ).fetchall()
    return {fila["ticker"]: round(fila["en_cartera"], 6) for fila in filas}
