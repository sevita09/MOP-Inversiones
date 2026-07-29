"""Lo que la cartera dibuja sobre el gráfico de un papel.

Dos capas distintas y complementarias:

- **PPC** (v6.2): las compras que siguen abiertas y su precio promedio. Es una
  foto del *estado* — dónde está el costo de lo que se tiene hoy.
- **Operaciones** (v7.2): todas las órdenes ejecutadas, compras y ventas,
  incluidas las de posiciones ya cerradas. Es el *historial* — sirve para
  revisar si se entró barato o se le compró al techo.

Las dos convierten los precios con `precio_para_vista`, o sea **con el CCL**,
aunque la cartera se valúe con MEP: estas marcas tienen que caer sobre la serie
que el gráfico está dibujando, y esa serie se convierte con CCL.
"""
from __future__ import annotations

import sqlite3
from datetime import datetime, timedelta, timezone
from typing import Optional

from app.repositorios import splits as repo_splits
from app.repositorios import transacciones as repo
from app.servicios.cartera.posiciones import lotes_pendientes
from app.servicios.dolar import precio_para_vista


def _fin_del_dia(fecha: str) -> int:
    """ts del último instante del día, para encontrar la vela de esa rueda."""
    dia = datetime.strptime(fecha, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    return int((dia + timedelta(days=1)).timestamp()) - 1


def _ts_de_la_rueda(conexion: sqlite3.Connection, ticker: str, fecha: str) -> Optional[int]:
    """El ts de la vela de esa fecha (o la anterior): es lo que ubica el chart."""
    fila = conexion.execute(
        """SELECT ts FROM velas
           WHERE ticker = ? AND temporalidad = 'D' AND ts <= ? AND es_faltante = 0
           ORDER BY ts DESC LIMIT 1""",
        (ticker, _fin_del_dia(fecha)),
    ).fetchone()
    return fila["ts"] if fila else None


def lotes_abiertos(conexion: sqlite3.Connection, ticker: str, moneda: str = "ARS") -> dict:
    """Los lotes de compra que siguen abiertos, con su PPC.

    Cada lote trae su fecha (y el ts de esa rueda), cuántos papeles quedan de esa
    compra tras el FIFO, y a qué costo unitario con gastos.
    """
    lotes = lotes_pendientes(
        repo.listar_cronologicas(conexion, ticker),
        repo_splits.listar_cronologicos(conexion, ticker),
    )
    if not lotes:
        return {"ticker": ticker, "moneda": moneda, "lotes": [], "ppc": None, "cantidad": 0}

    salida = []
    for lote in lotes:
        precio = precio_para_vista(
            conexion, ticker, lote["precio"] + lote["gasto_unitario"], lote["fecha"], moneda
        )
        if precio is None:
            continue  # sin dólar de esa fecha no se puede ubicar la compra
        salida.append(
            {
                "fecha": lote["fecha"],
                "ts": _ts_de_la_rueda(conexion, ticker, lote["fecha"]),
                "cantidad": round(lote["cantidad"], 6),
                "precio": round(precio, 6),
            }
        )

    cantidad = sum(l["cantidad"] for l in salida)
    costo = sum(l["cantidad"] * l["precio"] for l in salida)
    return {
        "ticker": ticker,
        "moneda": moneda,
        "lotes": salida,
        # Promedio ponderado de los lotes ya convertidos: en USD son los dólares
        # efectivamente puestos, no el promedio en pesos pasado por el dólar de hoy
        "ppc": round(costo / cantidad, 6) if cantidad else None,
        "cantidad": round(cantidad, 6),
    }


def operaciones_de(conexion: sqlite3.Connection, ticker: str, moneda: str = "ARS") -> dict:
    """Todas las operaciones del papel para marcarlas sobre el gráfico.

    A diferencia del PPC, acá entran **las ventas y las compras ya cerradas**:
    la pregunta es cómo se operó, no qué se tiene. El precio es el de mercado
    (sin gastos), que es el punto donde se ejecutó la orden y el comparable
    contra la vela.
    """
    operaciones = []
    for operacion in repo.listar_cronologicas(conexion, ticker):
        precio = precio_para_vista(
            conexion, ticker, operacion["precio"], operacion["fecha"], moneda
        )
        if precio is None:
            continue
        operaciones.append(
            {
                "id": operacion["id"],
                "tipo": operacion["tipo"],
                "fecha": operacion["fecha"],
                "ts": _ts_de_la_rueda(conexion, ticker, operacion["fecha"]),
                "cantidad": operacion["cantidad"],
                "precio": round(precio, 6),
                "nota": operacion["nota"],
            }
        )
    return {"ticker": ticker, "moneda": moneda, "operaciones": operaciones}
