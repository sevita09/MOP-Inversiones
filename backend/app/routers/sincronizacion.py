from __future__ import annotations

import sqlite3

from fastapi import APIRouter, Depends

from app.db import conexion_api
from app.repositorios.registro_sync import obtener_ultima_sync_global
from app.servicios.sincronizador import (
    hay_sync_en_curso,
    sincronizar_en_background,
    ultimo_resumen,
)

router = APIRouter(prefix="/api")


@router.post("/sync")
def lanzar_sync():
    if sincronizar_en_background():
        return {"estado": "iniciado"}
    return {"estado": "ya_en_curso"}


@router.get("/sync")
def estado_sync(conexion: sqlite3.Connection = Depends(conexion_api)):
    return {
        "en_curso": hay_sync_en_curso(),
        "ultima_sync": obtener_ultima_sync_global(conexion),
        "ultimo_resumen": ultimo_resumen(),
    }
