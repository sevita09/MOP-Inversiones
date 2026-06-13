from __future__ import annotations

import sqlite3
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException

from app.config import (
    CEDEARS,
    PANEL_GENERAL,
    PANEL_LIDER,
    TEMPORALIDADES,
    todos_los_tickers,
)
from app.db import conexion_api
from app.repositorios.velas import obtener_velas

router = APIRouter(prefix="/api")


@router.get("/tickers")
def tickers():
    return {
        "panel_lider": PANEL_LIDER,
        "panel_general": PANEL_GENERAL,
        "cedears": CEDEARS,
    }


@router.get("/velas")
def velas(
    ticker: str,
    temporalidad: str = "D",
    desde: Optional[int] = None,
    hasta: Optional[int] = None,
    conexion: sqlite3.Connection = Depends(conexion_api),
):
    if temporalidad not in TEMPORALIDADES:
        raise HTTPException(422, f"Temporalidad inválida: {temporalidad} (usar H, D, S o M)")
    if ticker not in todos_los_tickers():
        raise HTTPException(404, f"Ticker desconocido: {ticker}")
    return {
        "ticker": ticker,
        "temporalidad": temporalidad,
        "velas": obtener_velas(conexion, ticker, temporalidad, desde, hasta),
    }
