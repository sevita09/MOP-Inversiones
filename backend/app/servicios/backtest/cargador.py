"""Carga de datos para el backtest.

Igual que el resto del motor de bots, el backtest ve LO MISMO que el chart:
velas de `velas_para_vista` (moneda y ADR resueltos) e indicadores del registry.
La historia se carga COMPLETA para que los indicadores lleguen calientes (warmup)
al inicio del rango; recién después se recorta la simulación al rango pedido.
"""
from __future__ import annotations

import sqlite3
from typing import Optional

from app.esquemas.reglas import Reglas
from app.servicios.bots.evaluador import temporalidades_de
from app.servicios.dolar import velas_para_vista


def cargar_historia(conexion: sqlite3.Connection, bot: dict) -> tuple[Reglas, dict, list[dict]]:
    """Devuelve (reglas, velas_por_temporalidad, velas_de_la_temporalidad_del_bot).

    `velas_por` trae la historia completa de cada temporalidad que usan las
    reglas (para el warmup de los indicadores en la confluencia).
    """
    reglas = Reglas(**bot["reglas"])
    velas_por = {
        tf: velas_para_vista(conexion, bot["ticker"], tf, bot["moneda"])
        for tf in temporalidades_de(reglas, bot["temporalidad"])
    }
    return reglas, velas_por, velas_por.get(bot["temporalidad"], [])


def recortar(velas: list[dict], desde: Optional[int], hasta: Optional[int]) -> list[dict]:
    """Las barras de la simulación: las velas dentro del rango [desde, hasta]."""
    return [
        v
        for v in velas
        if (desde is None or v["ts"] >= desde) and (hasta is None or v["ts"] <= hasta)
    ]
