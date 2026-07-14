from __future__ import annotations

import sqlite3

from fastapi import APIRouter, Depends, HTTPException

from app.config import TICKERS_DOLAR
from app.db import conexion_api
from app.esquemas.bots import BotEdicion, BotPeticion
from app.repositorios import bots as repo
from app.servicios.tickers_extra import universo_completo

router = APIRouter(prefix="/api")


def _validar_ticker(conexion: sqlite3.Connection, ticker: str) -> str:
    """Los bots operan cualquier ticker con datos, menos los de dólar."""
    ticker = ticker.upper()
    if ticker in TICKERS_DOLAR or ticker not in universo_completo(conexion):
        raise HTTPException(422, f"Ticker inválido para bots: {ticker}")
    return ticker


@router.get("/bots")
def listar_bots(conexion: sqlite3.Connection = Depends(conexion_api)):
    return repo.listar(conexion)


@router.get("/bots/{id_bot}")
def obtener_bot(id_bot: int, conexion: sqlite3.Connection = Depends(conexion_api)):
    bot = repo.obtener(conexion, id_bot)
    if bot is None:
        raise HTTPException(404, "Bot no encontrado")
    return bot


@router.post("/bots", status_code=201)
def crear_bot(body: BotPeticion, conexion: sqlite3.Connection = Depends(conexion_api)):
    nombre = body.nombre.strip()
    if not nombre:
        raise HTTPException(422, "El nombre no puede estar vacío")
    ticker = _validar_ticker(conexion, body.ticker)
    bot = repo.crear(
        conexion,
        nombre,
        ticker,
        body.temporalidad,
        body.moneda,
        body.capital.model_dump(),
        activo=body.activo,
    )
    if bot is None:
        raise HTTPException(409, f"Ya existe un bot llamado {nombre}")
    return bot


@router.put("/bots/{id_bot}")
def editar_bot(
    id_bot: int, body: BotEdicion, conexion: sqlite3.Connection = Depends(conexion_api)
):
    cambios = body.model_dump(exclude_none=True)
    if "nombre" in cambios:
        cambios["nombre"] = cambios["nombre"].strip()
        if not cambios["nombre"]:
            raise HTTPException(422, "El nombre no puede estar vacío")
    if "ticker" in cambios:
        cambios["ticker"] = _validar_ticker(conexion, cambios["ticker"])
    bot = repo.actualizar(conexion, id_bot, cambios)
    if bot is False:
        raise HTTPException(404, "Bot no encontrado")
    if bot is None:
        raise HTTPException(409, f"Ya existe un bot llamado {cambios['nombre']}")
    return bot


@router.delete("/bots/{id_bot}")
def eliminar_bot(id_bot: int, conexion: sqlite3.Connection = Depends(conexion_api)):
    if not repo.eliminar(conexion, id_bot):
        raise HTTPException(404, "Bot no encontrado")
    return {"ok": True}


@router.post("/bots/{id_bot}/duplicar", status_code=201)
def duplicar_bot(id_bot: int, conexion: sqlite3.Connection = Depends(conexion_api)):
    copia = repo.duplicar(conexion, id_bot)
    if copia is None:
        raise HTTPException(404, "Bot no encontrado")
    return copia
