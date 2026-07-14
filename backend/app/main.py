from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.db import inicializar_base
from app.rutas import dir_recursos
from app.routers import (
    actualizacion,
    bots,
    categorias,
    dibujos,
    dolar,
    indicadores,
    logos,
    mercado,
    niveles,
    reparacion,
    sincronizacion,
    tickers_extra,
)
from app.servicios.logos import asegurar_logos_en_background
from app.servicios.programador import iniciar_programador
from app.servicios.respaldos import respaldar_base
from app.servicios.sincronizador import sincronizar_en_background


@asynccontextmanager
async def lifespan(_app: FastAPI):
    # Respaldar antes de tocar la base: si un arranque la corrompe, hay vuelta atrás
    respaldar_base()
    inicializar_base()
    sincronizar_en_background()
    iniciar_programador()  # re-sincroniza cada 15 min en rueda, cada hora fuera
    asegurar_logos_en_background()  # baja los logos que falten, sin bloquear
    yield


app = FastAPI(title="MOP Inversiones", lifespan=lifespan)
app.include_router(actualizacion.router)
app.include_router(bots.router)
app.include_router(categorias.router)
app.include_router(dibujos.router)
app.include_router(dolar.router)
app.include_router(indicadores.router)
app.include_router(logos.router)
app.include_router(mercado.router)
app.include_router(niveles.router)
app.include_router(reparacion.router)
app.include_router(sincronizacion.router)
app.include_router(tickers_extra.router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/salud")
def salud():
    return {"estado": "ok", "servicio": "mop-backend"}


# Frontend compilado (modo app de escritorio): servir el build de Vite desde el
# mismo puerto que la API, así todo corre en un solo origen sin CORS. Se monta al
# final para que las rutas /api tengan prioridad, y solo si existe el build (en
# desarrollo con Vite y en los tests no hace falta).
_FRONTEND_DIST = dir_recursos() / "frontend" / "dist"
if _FRONTEND_DIST.is_dir():
    app.mount("/", StaticFiles(directory=_FRONTEND_DIST, html=True), name="frontend")
