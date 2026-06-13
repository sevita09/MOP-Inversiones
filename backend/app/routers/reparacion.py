import sqlite3

from fastapi import APIRouter, Depends

from app.db import conexion_api
from app.repositorios.velas import contar_faltantes
from app.servicios.reparador import reparar_todo

router = APIRouter(prefix="/api")


@router.get("/faltantes")
def faltantes(conexion: sqlite3.Connection = Depends(conexion_api)):
    detalle = contar_faltantes(conexion)
    return {"total": sum(fila["faltantes"] for fila in detalle), "detalle": detalle}


@router.post("/reparar")
def reparar(conexion: sqlite3.Connection = Depends(conexion_api)):
    return reparar_todo(conexion)
