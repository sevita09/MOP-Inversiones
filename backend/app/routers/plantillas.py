"""Plantillas de estrategia: las 4 de la metodología + las propias del usuario.

Router propio (no cuelga de /api/bots) a propósito: un literal como
`/api/bots/plantillas` compite con `/api/bots/{id_bot}` y obliga a cuidar el
orden de declaración para siempre. Con prefijo propio, esa clase de error no
puede ocurrir.
"""
from __future__ import annotations

import sqlite3

from fastapi import APIRouter, Depends, HTTPException

from app.db import conexion_api
from app.esquemas.bots import PlantillaPeticion
from app.repositorios import plantillas as repo
from app.servicios.bots.plantillas import listar_plantillas

router = APIRouter(prefix="/api/plantillas")


def _propia_a_salida(plantilla: dict) -> dict:
    """Da a una plantilla del usuario la misma forma que las predefinidas."""
    return {
        "clave": f"custom:{plantilla['id']}",
        "id": plantilla["id"],
        "nombre": plantilla["nombre"],
        "descripcion": plantilla["descripcion"],
        "horizonte": "Plantilla propia",
        "temporalidad": plantilla["temporalidad"],
        "moneda": plantilla["moneda"],
        "reglas": plantilla["reglas"],
        "predefinida": False,
    }


@router.get("")
def listar(conexion: sqlite3.Connection = Depends(conexion_api)):
    """Las 4 estrategias de la metodología + las plantillas propias del usuario."""
    predefinidas = [{**p, "id": None, "predefinida": True} for p in listar_plantillas()]
    propias = [_propia_a_salida(p) for p in repo.listar(conexion)]
    return predefinidas + propias


@router.post("", status_code=201)
def crear(body: PlantillaPeticion, conexion: sqlite3.Connection = Depends(conexion_api)):
    """Guarda una estrategia propia para reusarla como plantilla."""
    nombre = body.nombre.strip()
    if not nombre:
        raise HTTPException(422, "El nombre no puede estar vacío")
    if any(p["nombre"] == nombre for p in listar_plantillas()):
        raise HTTPException(409, f"Ya existe una plantilla de la metodología llamada {nombre}")
    creada = repo.crear(
        conexion,
        nombre,
        body.descripcion.strip(),
        body.temporalidad,
        body.moneda,
        body.reglas.model_dump(exclude_none=True),
    )
    if creada is None:
        raise HTTPException(409, f"Ya existe una plantilla llamada {nombre}")
    return _propia_a_salida(creada)


@router.delete("/{id_plantilla}")
def eliminar(id_plantilla: int, conexion: sqlite3.Connection = Depends(conexion_api)):
    if not repo.eliminar(conexion, id_plantilla):
        raise HTTPException(404, "Plantilla no encontrada")
    return {"ok": True}
