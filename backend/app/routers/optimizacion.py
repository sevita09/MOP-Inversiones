"""Optimización de parámetros de un bot (grid search en background).

Router propio (no cuelga de /api/bots): un literal como `/api/bots/optimizacion`
compite con `/api/bots/{id_bot}` y obliga a cuidar el orden de declaración para
siempre. Con prefijo propio, esa clase de error no puede ocurrir.
"""
from __future__ import annotations

import sqlite3

from fastapi import APIRouter, Depends, HTTPException

from app.db import conexion_api
from app.esquemas.bots import OptimizacionPeticion
from app.repositorios import bots as repo
from app.servicios.backtest.trabajo_optimizacion import (
    estado_optimizacion,
    lanzar_optimizacion,
)

router = APIRouter(prefix="/api/optimizacion")


@router.get("")
def progreso():
    """Estado de la optimización en curso (o el resultado de la última)."""
    return estado_optimizacion()


@router.post("/{id_bot}", status_code=202)
def optimizar(
    id_bot: int,
    body: OptimizacionPeticion,
    conexion: sqlite3.Connection = Depends(conexion_api),
):
    """Lanza el grid search en background; el progreso se consulta aparte."""
    bot = repo.obtener(conexion, id_bot)
    if bot is None:
        raise HTTPException(404, "Bot no encontrado")
    if not bot["reglas"].get("entrada"):
        raise HTTPException(422, "El bot no tiene reglas de entrada para optimizar")

    parametros = [p.model_dump(exclude_none=True) for p in body.parametros]
    for param in parametros:
        if param["tipo"] == "condicion":
            if param.get("bloque") is None or param.get("indice") is None:
                raise HTTPException(422, "Una condición necesita bloque e índice")
            bloque = bot["reglas"].get(param["bloque"], [])
            if param["indice"] >= len(bloque):
                raise HTTPException(422, f"El bot no tiene esa condición en {param['bloque']}")

    if not lanzar_optimizacion(bot, parametros, body.metrica):
        raise HTTPException(409, "Ya hay una optimización en curso")
    return {"lanzada": True}
