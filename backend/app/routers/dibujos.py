from __future__ import annotations

import sqlite3

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.db import conexion_api
from app.repositorios import dibujos as repo

router = APIRouter(prefix="/api")

TIPOS_VALIDOS = {"horizontal", "tendencia", "fibonacci", "medicion"}


class DibujoPeticion(BaseModel):
    ticker: str
    tipo: str
    datos: dict


class DibujoActualizar(BaseModel):
    datos: dict


@router.get("/dibujos")
def listar_dibujos(ticker: str, conexion: sqlite3.Connection = Depends(conexion_api)):
    return repo.listar(conexion, ticker)


@router.post("/dibujos", status_code=201)
def crear_dibujo(body: DibujoPeticion, conexion: sqlite3.Connection = Depends(conexion_api)):
    if body.tipo not in TIPOS_VALIDOS:
        raise HTTPException(422, f"Tipo inválido: {body.tipo} (usar {', '.join(sorted(TIPOS_VALIDOS))})")
    return repo.crear(conexion, body.ticker, body.tipo, body.datos)


@router.put("/dibujos/{id_dibujo}")
def actualizar_dibujo(
    id_dibujo: int, body: DibujoActualizar, conexion: sqlite3.Connection = Depends(conexion_api)
):
    if not repo.actualizar(conexion, id_dibujo, body.datos):
        raise HTTPException(404, "Dibujo no encontrado")
    return {"ok": True}


@router.delete("/dibujos/{id_dibujo}")
def eliminar_dibujo(id_dibujo: int, conexion: sqlite3.Connection = Depends(conexion_api)):
    if not repo.eliminar(conexion, id_dibujo):
        raise HTTPException(404, "Dibujo no encontrado")
    return {"ok": True}
