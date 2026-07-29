"""Rendimiento de la cartera: qué se ganó de verdad, ya con la plata en la mano.

El P&L **realizado** es el de las operaciones cerradas: cada venta contra el
costo de las compras que consumió por FIFO. Es distinto del no realizado de
`posiciones.py` (lo que valdría vender hoy) y no se pisa con él: un papel puede
tener las dos cosas si se vendió una parte.

**En USD cada tramo va con el MEP de su propia fecha**: los dólares que se
pusieron al comprar contra los que se sacaron al vender. Convertir el resultado
en pesos con el dólar de hoy daría un número que nunca existió (la misma regla
que rige las marcas del gráfico en v6.2).
"""
from __future__ import annotations

import sqlite3
from typing import Optional

from app.repositorios import splits as repo_splits
from app.repositorios import transacciones as repo
from app.repositorios.tasas_dolar import obtener_tasa_en_fecha
from app.servicios.cartera import TIPO_DOLAR
from app.servicios.cartera.posiciones import recorrer_fifo


def _porcentaje(pnl: float, costo: float) -> Optional[float]:
    return round(pnl / costo * 100, 2) if costo else None


def _venta_realizada(conexion: sqlite3.Connection, venta: dict) -> dict:
    """Resultado de una venta: lo que entró menos lo que habían costado esos papeles.

    Los gastos pesan de los dos lados: los de la compra ya están en el costo
    unitario del lote, y los de la venta se restan del ingreso.
    """
    ingreso = venta["cantidad"] * venta["precio"] - venta["comision"]
    costo = sum(c["cantidad"] * c["costo_unitario"] for c in venta["consumos"])

    tasa_venta = obtener_tasa_en_fecha(conexion, venta["fecha"], TIPO_DOLAR)
    ingreso_usd = ingreso / tasa_venta if tasa_venta else None
    costo_usd: Optional[float] = 0.0
    for consumo in venta["consumos"]:
        tasa_compra = obtener_tasa_en_fecha(conexion, consumo["fecha"], TIPO_DOLAR)
        if not tasa_compra or costo_usd is None:
            costo_usd = None  # sin MEP de esa compra no hay resultado en dólares
            continue
        costo_usd += consumo["cantidad"] * consumo["costo_unitario"] / tasa_compra

    pnl = ingreso - costo
    en_usd = ingreso_usd is not None and costo_usd is not None
    return {
        "id": venta["id"],
        "ticker": venta["ticker"],
        "fecha": venta["fecha"],
        "cantidad": round(venta["cantidad"], 6),
        "precio": venta["precio"],
        "ingreso": round(ingreso, 2),
        "costo": round(costo, 2),
        "ingreso_usd": round(ingreso_usd, 2) if en_usd else None,
        "costo_usd": round(costo_usd, 2) if en_usd else None,
        "pnl": round(pnl, 2),
        "pnl_pct": _porcentaje(pnl, costo),
        "pnl_usd": round(ingreso_usd - costo_usd, 2) if en_usd else None,
        "pnl_usd_pct": _porcentaje(ingreso_usd - costo_usd, costo_usd) if en_usd else None,
        # La compra más vieja que se consumió: cuánto tiempo estuvo puesta la plata
        "desde": venta["consumos"][0]["fecha"] if venta["consumos"] else None,
    }


def realizado_de(conexion: sqlite3.Connection, ticker: str) -> Optional[dict]:
    """P&L realizado de un papel, o None si nunca se vendió nada."""
    _, ventas = recorrer_fifo(
        repo.listar_cronologicas(conexion, ticker),
        repo_splits.listar_cronologicos(conexion, ticker),
    )
    if not ventas:
        return None

    detalle = [_venta_realizada(conexion, venta) for venta in ventas]
    costo = sum(v["costo"] for v in detalle)
    ingreso = sum(v["ingreso"] for v in detalle)
    pnl = ingreso - costo
    completo = all(v["pnl_usd"] is not None for v in detalle)
    costo_usd = sum(v["costo_usd"] for v in detalle) if completo else None
    ingreso_usd = sum(v["ingreso_usd"] for v in detalle) if completo else None

    return {
        "ticker": ticker,
        "operaciones": len(detalle),
        "cantidad": round(sum(v["cantidad"] for v in detalle), 6),
        "costo": round(costo, 2),
        "ingreso": round(ingreso, 2),
        "pnl": round(pnl, 2),
        "pnl_pct": _porcentaje(pnl, costo),
        # Solo hay cifras en dólares si todas las ventas tienen MEP en las dos puntas
        "costo_usd": round(costo_usd, 2) if completo else None,
        "ingreso_usd": round(ingreso_usd, 2) if completo else None,
        "pnl_usd": round(ingreso_usd - costo_usd, 2) if completo else None,
        "pnl_usd_pct": _porcentaje(ingreso_usd - costo_usd, costo_usd) if completo else None,
        "ventas": detalle,
    }


def realizado(conexion: sqlite3.Connection) -> dict:
    """P&L realizado de toda la cartera, por papel y en total."""
    papeles = []
    for ticker in repo.tickers_operados(conexion):
        resultado = realizado_de(conexion, ticker)
        if resultado:
            papeles.append(resultado)

    costo = sum(p["costo"] for p in papeles)
    ingreso = sum(p["ingreso"] for p in papeles)
    pnl = ingreso - costo
    completo = all(p["pnl_usd"] is not None for p in papeles)
    costo_usd = sum(p["costo_usd"] for p in papeles) if completo else None
    ingreso_usd = sum(p["ingreso_usd"] for p in papeles) if completo else None

    papeles.sort(key=lambda p: p["pnl"], reverse=True)
    return {
        "papeles": papeles,
        "totales": {
            "operaciones": sum(p["operaciones"] for p in papeles),
            "costo": round(costo, 2),
            "ingreso": round(ingreso, 2),
            "pnl": round(pnl, 2),
            "pnl_pct": _porcentaje(pnl, costo),
            "costo_usd": round(costo_usd, 2) if completo else None,
            "ingreso_usd": round(ingreso_usd, 2) if completo else None,
            "pnl_usd": round(ingreso_usd - costo_usd, 2) if completo else None,
            "pnl_usd_pct": _porcentaje(ingreso_usd - costo_usd, costo_usd) if completo else None,
        },
    }
