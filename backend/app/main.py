from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.db import inicializar_base
from app.servicios.respaldos import respaldar_base


@asynccontextmanager
async def lifespan(_app: FastAPI):
    # Respaldar antes de tocar la base: si un arranque la corrompe, hay vuelta atrás
    respaldar_base()
    inicializar_base()
    yield


app = FastAPI(title="MOP Inversiones", lifespan=lifespan)

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
