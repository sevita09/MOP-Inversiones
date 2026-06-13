from fastapi import APIRouter

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
def estado_sync():
    return {
        "en_curso": hay_sync_en_curso(),
        "ultimo_resumen": ultimo_resumen(),
    }
