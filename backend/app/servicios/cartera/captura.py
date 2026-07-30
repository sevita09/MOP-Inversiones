"""Captura del recorrido: cuánto se llevó cada venta de lo que el papel dio.

Contesta si el problema está en elegir el papel o en elegir cuándo salir: una
captura promedio baja con P&L positivo dice que las tesis eran buenas y las
salidas tempranas.

No confundir con el escenario "en el máximo" de `escenarios.py`, que busca el
mejor precio de toda la historia del papel —incluso posterior a la venta—. Acá
el recorrido es solo el que existió **mientras la posición estaba abierta**, que
es la información que había al momento de decidir.
"""
from __future__ import annotations

import sqlite3
from typing import Optional

from app.servicios.cartera.escenarios import maximo_entre, todas_las_ventas


def _captura_de(conexion: sqlite3.Connection, venta: dict) -> Optional[dict]:
    """Cuánto del recorrido disponible se llevó esa venta.

    El recorrido es lo que el papel dio **mientras se lo tuvo**: desde el costo
    de las compras consumidas hasta el cierre más alto entre esa compra y la
    venta. Salir en el techo es 100%; salir al costo, 0%.

    Queda en `None` cuando el papel nunca subió por encima del costo: no hubo
    recorrido que capturar y el porcentaje no significaría nada.
    """
    if not venta["consumos"]:
        return None
    cantidad = sum(c["cantidad"] for c in venta["consumos"])
    costo_unitario = (
        sum(c["cantidad"] * c["costo_unitario"] for c in venta["consumos"]) / cantidad
    )
    maximo = maximo_entre(
        conexion, venta["ticker"], venta["consumos"][0]["fecha"], venta["fecha"]
    )
    if maximo is None or maximo["precio"] <= costo_unitario:
        return None

    recorrido = maximo["precio"] - costo_unitario
    capturado = venta["precio"] - costo_unitario
    return {
        "id": venta["id"],
        "ticker": venta["ticker"],
        "fecha": venta["fecha"],
        "costo_unitario": round(costo_unitario, 4),
        "precio_venta": venta["precio"],
        "maximo": maximo["precio"],
        "maximo_fecha": maximo["fecha"],
        "captura_pct": round(capturado / recorrido * 100, 2),
    }


def captura_del_recorrido(conexion: sqlite3.Connection) -> dict:
    """Métrica de captura sobre todas las operaciones cerradas.

    Contesta si el problema está en elegir el papel o en elegir cuándo salir:
    una captura promedio baja con P&L positivo dice que las tesis eran buenas y
    las salidas tempranas.
    """
    operaciones = []
    for venta in todas_las_ventas(conexion):
        captura = _captura_de(conexion, venta)
        if captura:
            operaciones.append(captura)

    operaciones.sort(key=lambda o: o["fecha"], reverse=True)
    valores = [o["captura_pct"] for o in operaciones]
    return {
        "operaciones": operaciones,
        "promedio_pct": round(sum(valores) / len(valores), 2) if valores else None,
        "medidas": len(valores),
    }



