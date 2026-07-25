from __future__ import annotations

import sqlite3

from fastapi import APIRouter, Depends, HTTPException

from app.db import conexion_api
from app.esquemas.bots import PresetRiesgoPeticion
from app.repositorios import presets_riesgo as repo

router = APIRouter(prefix="/api/riesgo")


@router.get("/presets")
def listar_presets(conexion: sqlite3.Connection = Depends(conexion_api)):
    return repo.listar(conexion)


@router.post("/presets", status_code=201)
def crear_preset(
    body: PresetRiesgoPeticion, conexion: sqlite3.Connection = Depends(conexion_api)
):
    nombre = body.nombre.strip()
    if not nombre:
        raise HTTPException(422, "El nombre no puede estar vacío")
    preset = repo.crear(conexion, nombre, body.riesgo.model_dump())
    if preset is None:
        raise HTTPException(409, f"Ya existe un preset de riesgo llamado {nombre}")
    return preset


@router.delete("/presets/{id_preset}")
def eliminar_preset(id_preset: int, conexion: sqlite3.Connection = Depends(conexion_api)):
    if not repo.eliminar(conexion, id_preset):
        raise HTTPException(404, "Preset no encontrado")
    return {"ok": True}
