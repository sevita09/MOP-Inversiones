from __future__ import annotations

import sqlite3

from fastapi import APIRouter, Depends, HTTPException

from app.db import conexion_api
from app.repositorios import senales as repo
from app.servicios.bots.senales import anotar_vigencia, ids_vencidas

router = APIRouter(prefix="/api")


@router.get("/senales")
def listar_senales(conexion: sqlite3.Connection = Depends(conexion_api)):
    """Señales (más nuevas primero) anotadas con si la entrada sigue vigente,
    más cuántas quedan sin ver."""
    senales = anotar_vigencia(conexion, repo.listar(conexion))
    return {"senales": senales, "sin_ver": repo.contar_sin_ver(conexion)}


@router.post("/senales/vistas")
def marcar_vistas(conexion: sqlite3.Connection = Depends(conexion_api)):
    """Marca todas las señales como vistas (al abrir la página se apaga el badge)."""
    return {"marcadas": repo.marcar_todas_vistas(conexion)}


@router.post("/senales/eliminar_vencidas")
def eliminar_vencidas(conexion: sqlite3.Connection = Depends(conexion_api)):
    """Borra de una las señales cuya entrada ya no se cumple."""
    ids = ids_vencidas(conexion, repo.listar(conexion))
    return {"eliminadas": repo.eliminar_varias(conexion, ids)}


@router.delete("/senales/{id_senal}")
def eliminar_senal(id_senal: int, conexion: sqlite3.Connection = Depends(conexion_api)):
    if not repo.eliminar(conexion, id_senal):
        raise HTTPException(404, "Señal no encontrada")
    return {"ok": True}
