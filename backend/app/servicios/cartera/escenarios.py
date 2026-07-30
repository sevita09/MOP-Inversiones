"""¿Qué pasaba si vendía antes o después?

Sobre una venta ya hecha, se recalcula el resultado moviendo **solo la fecha de
salida**: los papeles y las compras que consumió por FIFO quedan fijos, y el
precio de venta pasa a ser el cierre de la rueda alternativa. Así la comparación
aísla la decisión de cuándo salir, que es lo único que se está cuestionando.

Los gastos de la venta alternativa se recalculan con las tasas del broker a esa
fecha, sin arancel de intradía: es una operación hipotética, no hay una
contraparte del mismo día con la que emparejarla.
"""
from __future__ import annotations

import sqlite3
from datetime import datetime, timedelta, timezone
from typing import Optional

from app.repositorios import splits as repo_splits
from app.repositorios import transacciones as repo
from app.servicios.cartera.comisiones import contexto, desde_precio
from app.servicios.cartera.posiciones import recorrer_fifo
from app.servicios.cartera.transacciones import precio_sugerido

# Desplazamientos automáticos de la tabla, en días corridos
DESPLAZAMIENTOS = [
    ("−3 meses", -90),
    ("−1 mes", -30),
    ("−1 semana", -7),
    ("+1 semana", 7),
    ("+1 mes", 30),
    ("+3 meses", 90),
]


def _mover(fecha: str, dias: int) -> str:
    dia = datetime.strptime(fecha, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    return (dia + timedelta(days=dias)).strftime("%Y-%m-%d")


def _hoy(conexion: sqlite3.Connection, ticker: str) -> Optional[str]:
    """La última rueda con datos del papel: el límite de cualquier escenario."""
    fila = conexion.execute(
        """SELECT ts FROM velas
           WHERE ticker = ? AND temporalidad = 'D' AND es_faltante = 0
           ORDER BY ts DESC LIMIT 1""",
        (ticker,),
    ).fetchone()
    if fila is None:
        return None
    return datetime.fromtimestamp(fila["ts"], tz=timezone.utc).strftime("%Y-%m-%d")


def maximo_entre(
    conexion: sqlite3.Connection, ticker: str, desde: str, hasta: str
) -> Optional[dict]:
    """El cierre más alto entre dos fechas, con la rueda en que ocurrió."""
    fila = conexion.execute(
        """SELECT ts, cierre FROM velas
           WHERE ticker = ? AND temporalidad = 'D' AND es_faltante = 0
             AND date(ts, 'unixepoch') BETWEEN ? AND ?
           ORDER BY cierre DESC LIMIT 1""",
        (ticker, desde, hasta),
    ).fetchone()
    if fila is None:
        return None
    return {
        "fecha": datetime.fromtimestamp(fila["ts"], tz=timezone.utc).strftime("%Y-%m-%d"),
        "precio": fila["cierre"],
    }


def _venta_por_id(conexion: sqlite3.Connection, id_venta: int) -> Optional[dict]:
    """La venta con los lotes que consumió, reconstruida por FIFO."""
    operacion = repo.obtener(conexion, id_venta)
    if operacion is None or operacion["tipo"] != "venta":
        return None
    _, ventas = recorrer_fifo(
        repo.listar_cronologicas(conexion, operacion["ticker"]),
        repo_splits.listar_cronologicos(conexion, operacion["ticker"]),
    )
    return next((v for v in ventas if v["id"] == id_venta), None)


def _resultado(
    conexion: sqlite3.Connection,
    venta: dict,
    precio: float,
    fecha: str,
    gastos: Optional[float] = None,
) -> dict:
    """P&L de vender esos papeles a ese precio en esa fecha.

    Con `gastos` se pasan los que se pagaron de verdad (el caso real); sin él se
    estiman con las tasas vigentes, que es lo que corresponde a un escenario.
    """
    if gastos is None:
        ctx = contexto(conexion, venta["ticker"], fecha, "venta")
        gastos = desde_precio(precio, venta["cantidad"], "venta", ctx, False)["gastos"]
    ingreso = venta["cantidad"] * precio - gastos
    costo = sum(c["cantidad"] * c["costo_unitario"] for c in venta["consumos"])
    pnl = ingreso - costo
    return {
        "fecha": fecha,
        "precio": round(precio, 4),
        "ingreso": round(ingreso, 2),
        "costo": round(costo, 2),
        "pnl": round(pnl, 2),
        "pnl_pct": round(pnl / costo * 100, 2) if costo else None,
    }


def _primera_compra(venta: dict) -> str:
    return venta["consumos"][0]["fecha"] if venta["consumos"] else venta["fecha"]


def _alternativo(
    conexion: sqlite3.Connection,
    venta: dict,
    fecha: str,
    primera_compra: str,
    limite: Optional[str],
) -> Optional[dict]:
    """El escenario en esa fecha, o None si cae fuera de lo posible.

    Trabaja sobre una venta ya resuelta: recorrer el FIFO de nuevo por cada
    escenario multiplicaba el trabajo por ocho en carteras con muchas ventas.
    """
    # No se puede vender antes de haber comprado ni después de la última rueda
    if fecha < primera_compra or (limite and fecha > limite):
        return None
    precio = precio_sugerido(conexion, venta["ticker"], fecha)
    if precio is None:
        return None
    return _resultado(conexion, venta, precio, fecha)


def pnl_con_fecha(
    conexion: sqlite3.Connection, id_venta: int, fecha: str
) -> Optional[dict]:
    """Resultado de esa venta si se hubiera hecho en otra fecha.

    Devuelve también la diferencia contra lo que pasó de verdad — el número que
    contesta la pregunta. `None` si la venta no existe o la fecha queda fuera de
    la historia del papel.
    """
    venta = _venta_por_id(conexion, id_venta)
    if venta is None:
        return None

    limite = _hoy(conexion, venta["ticker"])
    alternativo = _alternativo(
        conexion, venta, fecha, _primera_compra(venta), limite
    )
    if alternativo is None:
        return None
    real = _resultado(conexion, venta, venta["precio"], venta["fecha"], venta["comision"])
    return {
        "id": id_venta,
        "ticker": venta["ticker"],
        "cantidad": round(venta["cantidad"], 6),
        "real": real,
        "alternativo": alternativo,
        "diferencia": round(alternativo["pnl"] - real["pnl"], 2),
        "diferencia_pct": (
            round(alternativo["pnl_pct"] - real["pnl_pct"], 2)
            if alternativo["pnl_pct"] is not None and real["pnl_pct"] is not None
            else None
        ),
    }


def escenarios_de(conexion: sqlite3.Connection, id_venta: int) -> Optional[dict]:
    """Los escenarios automáticos de una venta, con la diferencia contra lo hecho."""
    venta = _venta_por_id(conexion, id_venta)
    return None if venta is None else escenarios_de_venta(conexion, venta)


def escenarios_de_venta(conexion: sqlite3.Connection, venta: dict) -> dict:
    """Escenarios de una venta ya resuelta por FIFO.

    Además de los desplazamientos fijos, dos que suelen doler: haber vendido en
    **el máximo** del período y **no haber vendido** (mantener hasta hoy).
    """
    id_venta = venta["id"]
    limite = _hoy(conexion, venta["ticker"])
    primera_compra = _primera_compra(venta)
    real = _resultado(conexion, venta, venta["precio"], venta["fecha"], venta["comision"])

    def _contra_lo_hecho(nombre: str, resultado: dict) -> dict:
        """Un escenario con su diferencia contra la venta real, en pesos y en puntos."""
        return {
            "nombre": nombre,
            **resultado,
            "diferencia": round(resultado["pnl"] - real["pnl"], 2),
            "diferencia_pct": (
                round(resultado["pnl_pct"] - real["pnl_pct"], 2)
                if resultado["pnl_pct"] is not None and real["pnl_pct"] is not None
                else None
            ),
        }

    escenarios = []
    for nombre, dias in DESPLAZAMIENTOS:
        alternativa = _alternativo(
            conexion, venta, _mover(venta["fecha"], dias), primera_compra, limite
        )
        if alternativa:
            escenarios.append(_contra_lo_hecho(nombre, alternativa))

    maximo = maximo_entre(conexion, venta["ticker"], primera_compra, limite or venta["fecha"])
    if maximo:
        escenarios.append(
            _contra_lo_hecho(
                "en el máximo",
                _resultado(conexion, venta, maximo["precio"], maximo["fecha"]),
            )
        )
    if limite and limite > venta["fecha"]:
        alternativa = _alternativo(conexion, venta, limite, primera_compra, limite)
        if alternativa:
            escenarios.append(_contra_lo_hecho("mantener hasta hoy", alternativa))

    return {
        "id": id_venta,
        "ticker": venta["ticker"],
        "cantidad": round(venta["cantidad"], 6),
        # El rango en que se puede mover la fecha de salida (lo usa el slider)
        "desde": primera_compra,
        "hasta": limite,
        "real": real,
        "escenarios": escenarios,
        # El mejor escenario alternativo: cuánto quedó sobre la mesa
        "mejor": max(escenarios, key=lambda e: e["pnl"]) if escenarios else None,
    }


def todas_las_ventas(conexion: sqlite3.Connection) -> list[dict]:
    """Las ventas de toda la cartera, con un solo recorrido FIFO por papel."""
    ventas = []
    for ticker in repo.tickers_operados(conexion):
        _, cerradas = recorrer_fifo(
            repo.listar_cronologicas(conexion, ticker),
            repo_splits.listar_cronologicos(conexion, ticker),
        )
        ventas += cerradas
    return ventas


def ventas_cerradas(conexion: sqlite3.Connection) -> dict:
    """Listado liviano de ventas, la más nueva primero: solo para elegir cuál mirar.

    Los escenarios de una venta se piden aparte (`escenarios_de`): calcularlos
    todos de entrada no escala — una cartera con cientos de operaciones pagaría
    ocho consultas por venta para mostrar una tabla que igual no se lee entera.
    """
    ventas = []
    for venta in todas_las_ventas(conexion):
        real = _resultado(conexion, venta, venta["precio"], venta["fecha"], venta["comision"])
        ventas.append(
            {
                "id": venta["id"],
                "ticker": venta["ticker"],
                "fecha": venta["fecha"],
                "cantidad": round(venta["cantidad"], 6),
                "desde": _primera_compra(venta),
                "pnl": real["pnl"],
                "pnl_pct": real["pnl_pct"],
            }
        )
    ventas.sort(key=lambda v: v["fecha"], reverse=True)
    return {"ventas": ventas}


def tabla_escenarios(conexion: sqlite3.Connection) -> dict:
    """Todas las ventas con sus escenarios, la más nueva primero.

    Es la vista completa (para revisar o exportar de una): la pantalla usa
    `ventas_cerradas` y pide el detalle de la venta elegida.
    """
    ventas = [escenarios_de_venta(conexion, v) for v in todas_las_ventas(conexion)]
    ventas.sort(key=lambda v: v["real"]["fecha"], reverse=True)
    return {"ventas": ventas}
