from fastapi import APIRouter

from app.servicios.actualizacion import estado_actualizacion
from app.version import VERSION

router = APIRouter(prefix="/api")


@router.get("/version")
def version():
    return {"version": VERSION}


@router.get("/actualizacion")
def actualizacion():
    return estado_actualizacion()
