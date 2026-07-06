from fastapi import APIRouter, HTTPException

from app.rutas import empaquetada
from app.servicios.actualizacion import estado_actualizacion
from app.servicios.instalador import instalar_actualizacion
from app.version import VERSION

router = APIRouter(prefix="/api")


@router.get("/version")
def version():
    return {"version": VERSION}


@router.get("/actualizacion")
def actualizacion():
    return estado_actualizacion()


@router.post("/actualizacion/instalar")
def instalar():
    """Instala la última release: la app se cierra sola y reabre actualizada."""
    if not empaquetada():
        raise HTTPException(409, "Solo disponible en la app instalada")
    try:
        return instalar_actualizacion()
    except ValueError as error:
        raise HTTPException(409, str(error))
