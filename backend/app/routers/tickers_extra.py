from __future__ import annotations

import sqlite3

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.db import conexion_api
from app.repositorios import tickers_extra as repo
from app.servicios.logos import descargar_logo_extra_en_background
from app.servicios.sincronizador import sincronizar_en_background
from app.servicios.tickers_extra import agregar_ticker

router = APIRouter(prefix="/api")


class TickerNuevo(BaseModel):
    ticker: str
    grupo: str


@router.post("/tickers_extra", status_code=201)
def agregar(body: TickerNuevo, conexion: sqlite3.Connection = Depends(conexion_api)):
    """Agrega un ticker nuevo: valida, descarga su historia y su logo en background."""
    try:
        resultado = agregar_ticker(conexion, body.ticker, body.grupo)
    except ValueError as error:
        raise HTTPException(422, str(error))
    sincronizar_en_background()  # baja la historia del nuevo (el resto está vigente)
    descargar_logo_extra_en_background(resultado["ticker"], resultado["grupo"])
    return resultado


@router.delete("/tickers_extra/{ticker}")
def eliminar(ticker: str, conexion: sqlite3.Connection = Depends(conexion_api)):
    if not repo.eliminar(conexion, ticker.upper()):
        raise HTTPException(404, f"{ticker.upper()} no está entre los agregados")
    return {"ok": True}
