"""Reglas de las operaciones de cartera: validación y precio sugerido.

El precio se carga en ARS (así se opera en BYMA). Al elegir ticker y fecha, la
app propone el cierre de esa rueda para no tener que buscarlo a mano — pero es
solo una sugerencia: el precio real de la orden (con su spread) lo pone el
usuario.
"""
from __future__ import annotations

import sqlite3
from datetime import datetime, timedelta, timezone
from typing import Optional

from app.repositorios.tasas_dolar import obtener_tasa_en_fecha

TIPOS = ("compra", "venta")


def fecha_valida(fecha: str) -> bool:
    try:
        datetime.strptime(fecha, "%Y-%m-%d")
        return True
    except (ValueError, TypeError):
        return False


def _fin_del_dia(fecha: str) -> int:
    """ts del último instante del día, para buscar la vela de esa rueda."""
    dia = datetime.strptime(fecha, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    return int((dia + timedelta(days=1)).timestamp()) - 1


def precio_sugerido(
    conexion: sqlite3.Connection, ticker: str, fecha: str
) -> Optional[float]:
    """Cierre de la rueda de esa fecha en ARS.

    Si ese día no hubo rueda (fin de semana o feriado), devuelve el de la última
    anterior. None si no hay ninguna vela previa.
    """
    if not fecha_valida(fecha):
        return None
    fila = conexion.execute(
        """SELECT cierre FROM velas
           WHERE ticker = ? AND temporalidad = 'D' AND ts <= ? AND es_faltante = 0
           ORDER BY ts DESC LIMIT 1""",
        (ticker, _fin_del_dia(fecha)),
    ).fetchone()
    return fila["cierre"] if fila else None


def a_usd(conexion: sqlite3.Connection, monto_ars: float, fecha: str) -> Optional[float]:
    """Convierte un monto en ARS a USD con el CCL vigente en esa fecha."""
    tasa = obtener_tasa_en_fecha(conexion, fecha)
    return None if not tasa else round(monto_ars / tasa, 4)


def enriquecer(conexion: sqlite3.Connection, transaccion: dict) -> dict:
    """Suma a la operación sus totales y el equivalente en USD del día.

    - `bruto`: cantidad × precio, sin comisión (lo que valen los papeles).
    - `monto_final`: lo que efectivamente pagó o cobró (bruto ± comisión).
    """
    bruto = transaccion["cantidad"] * transaccion["precio"]
    # La comisión encarece la compra y achica lo cobrado en la venta
    monto_final = (
        bruto + transaccion["comision"]
        if transaccion["tipo"] == "compra"
        else bruto - transaccion["comision"]
    )
    return {
        **transaccion,
        "bruto": round(bruto, 2),
        "monto_final": round(monto_final, 2),
        "monto_final_usd": a_usd(conexion, monto_final, transaccion["fecha"]),
    }
