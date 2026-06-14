from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.db import inicializar_base
from app.routers import dolar, mercado, reparacion, sincronizacion
from app.servicios.respaldos import respaldar_base
from app.servicios.sincronizador import sincronizar_en_background


@asynccontextmanager
async def lifespan(_app: FastAPI):
    # Respaldar antes de tocar la base: si un arranque la corrompe, hay vuelta atrás
    respaldar_base()
    inicializar_base()
    sincronizar_en_background()
    yield


app = FastAPI(title="MOP Inversiones", lifespan=lifespan)
app.include_router(dolar.router)
app.include_router(mercado.router)
app.include_router(reparacion.router)
app.include_router(sincronizacion.router)

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
