"""Tenencias por FIFO: qué se tiene hoy, a qué costo y cuánto vale.

**FIFO** (primero entrado, primero salido) es el criterio del fisco argentino y
el que corresponde: al vender se consumen las compras más viejas. Las que quedan
sin consumir son la posición actual, y su costo es el costo real de esos papeles
—no un promedio de toda la historia.

Los **gastos entran al costo**: una compra de 100 papeles a $1.000 con $500 de
gastos cuesta $100.500, o sea $1.005 por papel. Al vender parcialmente, los
gastos se prorratean por unidad, así el costo de lo que queda es el correcto.
Ignorarlos daría un P&L optimista que no existe.
"""
from __future__ import annotations

import sqlite3
from typing import Optional

from app.repositorios import splits as repo_splits
from app.repositorios import transacciones as repo
from app.repositorios.tasas_dolar import obtener_tasa_en_fecha
from app.servicios.cartera import TIPO_DOLAR


def eventos_ordenados(operaciones: list[dict], splits: list[dict]) -> list[dict]:
    """Operaciones y splits mezclados en orden cronológico.

    Un split del mismo día que una compra se aplica DESPUÉS (la compra se hizo
    con el precio viejo de esa rueda), de ahí el 1 contra el 0 al desempatar.
    """
    eventos = [{**o, "_orden": (o["fecha"], 0, o["id"])} for o in operaciones]
    eventos += [{**s, "tipo": "split", "_orden": (s["fecha"], 1, s["id"])} for s in splits]
    return sorted(eventos, key=lambda e: e["_orden"])


def recorrer_fifo(
    operaciones: list[dict], splits: list[dict]
) -> tuple[list[dict], list[dict]]:
    """Recorre los eventos en orden y devuelve `(lotes abiertos, ventas cerradas)`.

    Los lotes abiertos son las compras que quedaron sin vender, cada una con su
    costo unitario con gastos: son la tenencia de hoy. Cada venta anota qué
    lotes consumió y a qué costo — eso es lo que vuelve calculable el P&L
    **realizado** (v7.1) sin volver a recorrer nada.
    """
    lotes: list[dict] = []
    ventas: list[dict] = []
    for evento in eventos_ordenados(operaciones, splits):
        if evento["tipo"] == "split":
            # Multiplica los papeles y divide su precio: el costo total no cambia
            ratio = evento["ratio"]
            for lote in lotes:
                lote["cantidad"] *= ratio
                lote["precio"] /= ratio
                lote["gasto_unitario"] /= ratio
            continue

        cantidad = evento["cantidad"]
        # Gasto por unidad: así una venta parcial se lleva su parte proporcional
        gasto_unitario = evento["comision"] / cantidad if cantidad else 0

        if evento["tipo"] == "compra":
            lotes.append(
                {
                    "cantidad": cantidad,
                    "precio": evento["precio"],
                    "gasto_unitario": gasto_unitario,
                    "fecha": evento["fecha"],
                }
            )
            continue

        # Venta: consume los lotes más viejos primero
        por_vender = cantidad
        consumos = []
        while por_vender > 1e-9 and lotes:
            lote = lotes[0]
            usado = min(lote["cantidad"], por_vender)
            consumos.append(
                {
                    "fecha": lote["fecha"],
                    "cantidad": usado,
                    "costo_unitario": lote["precio"] + lote["gasto_unitario"],
                }
            )
            lote["cantidad"] -= usado
            por_vender -= usado
            if lote["cantidad"] <= 1e-9:
                lotes.pop(0)
        ventas.append(
            {
                "id": evento["id"],
                "ticker": evento["ticker"],
                "fecha": evento["fecha"],
                "cantidad": cantidad,
                "precio": evento["precio"],
                "comision": evento["comision"],
                "consumos": consumos,
            }
        )
    return lotes, ventas


def lotes_pendientes(operaciones: list[dict], splits: list[dict]) -> list[dict]:
    """Solo los lotes abiertos (lo que se tiene hoy)."""
    return recorrer_fifo(operaciones, splits)[0]


def _precio_actual(conexion: sqlite3.Connection, ticker: str) -> Optional[float]:
    """Último cierre diario conocido, en ARS."""
    fila = conexion.execute(
        """SELECT cierre FROM velas
           WHERE ticker = ? AND temporalidad = 'D' AND es_faltante = 0
           ORDER BY ts DESC LIMIT 1""",
        (ticker,),
    ).fetchone()
    return fila["cierre"] if fila else None


def _tasa_hoy(conexion: sqlite3.Connection) -> Optional[float]:
    fila = conexion.execute(
        "SELECT fecha FROM tasas_dolar WHERE tipo = ? ORDER BY fecha DESC LIMIT 1",
        (TIPO_DOLAR,),
    ).fetchone()
    return obtener_tasa_en_fecha(conexion, fila["fecha"], TIPO_DOLAR) if fila else None


def posicion_de(conexion: sqlite3.Connection, ticker: str) -> Optional[dict]:
    """Tenencia actual de un papel, o None si no queda nada."""
    lotes = lotes_pendientes(
        repo.listar_cronologicas(conexion, ticker),
        repo_splits.listar_cronologicos(conexion, ticker),
    )
    cantidad = sum(lote["cantidad"] for lote in lotes)
    if cantidad <= 1e-9:
        return None

    costo = sum(lote["cantidad"] * (lote["precio"] + lote["gasto_unitario"]) for lote in lotes)
    precio = _precio_actual(conexion, ticker)
    valor = cantidad * precio if precio is not None else None

    return {
        "ticker": ticker,
        "cantidad": round(cantidad, 6),
        "costo": round(costo, 2),
        # Lo que costó cada papel de los que quedan, gastos incluidos
        "precio_promedio": round(costo / cantidad, 4),
        "precio_actual": precio,
        "valor_actual": None if valor is None else round(valor, 2),
        "pnl": None if valor is None else round(valor - costo, 2),
        "pnl_pct": None if valor is None or not costo else round((valor / costo - 1) * 100, 2),
        "desde": lotes[0]["fecha"],  # la compra más vieja que sigue abierta
    }


def tenencias(conexion: sqlite3.Connection) -> dict:
    """Todas las posiciones abiertas, con los totales de la cartera.

    El P&L en USD se calcula con el MEP de hoy sobre el resultado en ARS: es
    cuánto vale hoy en dólares la ganancia, no el resultado medido en dólares
    desde el inicio (eso llega en v7 con la curva de rendimiento).
    """
    posiciones = []
    for ticker in repo.tickers_operados(conexion):
        posicion = posicion_de(conexion, ticker)
        if posicion:
            posiciones.append(posicion)

    costo_total = sum(p["costo"] for p in posiciones)
    valor_total = sum(p["valor_actual"] for p in posiciones if p["valor_actual"] is not None)
    tasa = _tasa_hoy(conexion)

    # Peso de cada papel sobre el valor de mercado de la cartera
    for posicion in posiciones:
        valor = posicion["valor_actual"]
        posicion["peso_pct"] = (
            round(valor / valor_total * 100, 2) if valor and valor_total else None
        )
        posicion["valor_usd"] = round(valor / tasa, 2) if valor and tasa else None
        posicion["pnl_usd"] = (
            round(posicion["pnl"] / tasa, 2) if posicion["pnl"] is not None and tasa else None
        )

    posiciones.sort(key=lambda p: p["valor_actual"] or 0, reverse=True)
    pnl_total = valor_total - costo_total

    return {
        "posiciones": posiciones,
        "totales": {
            "costo": round(costo_total, 2),
            "valor_actual": round(valor_total, 2),
            "pnl": round(pnl_total, 2),
            "pnl_pct": round(pnl_total / costo_total * 100, 2) if costo_total else None,
            "valor_usd": round(valor_total / tasa, 2) if tasa else None,
            "pnl_usd": round(pnl_total / tasa, 2) if tasa else None,
            "tasa_ccl": tasa,
        },
    }


def cantidades_en_cartera(conexion: sqlite3.Connection) -> dict:
    """Papeles disponibles por ticker, ya ajustados por splits.

    Vive acá y no en el repositorio porque una suma SQL de compras menos ventas
    ignoraría los splits y daría la cantidad vieja.
    """
    return {p["ticker"]: p["cantidad"] for p in tenencias(conexion)["posiciones"]}
