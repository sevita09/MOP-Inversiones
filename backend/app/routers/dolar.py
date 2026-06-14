import sqlite3

from fastapi import APIRouter, Depends

from app.db import conexion_api
from app.repositorios.tasas_dolar import CCL, OFICIAL, obtener_ultima_tasa

router = APIRouter(prefix="/api")


@router.get("/dolar")
def dolar(conexion: sqlite3.Connection = Depends(conexion_api)):
    return {
        "ccl": obtener_ultima_tasa(conexion, CCL),
        "oficial": obtener_ultima_tasa(conexion, OFICIAL),
    }
