from __future__ import annotations

import sqlite3

from fastapi import APIRouter, Depends, HTTPException

from app.db import conexion_api
from app.servicios.estacionalidad import por_dia_semana, por_mes
from app.servicios.tickers_extra import universo_completo

router = APIRouter(prefix="/api/analisis")

MONEDAS = ("ARS", "USD")
VISTAS = {"mes": por_mes, "dia_semana": por_dia_semana}


@router.get("/estacionalidad")
def estacionalidad(
    ticker: str,
    moneda: str = "USD",
    vista: str = "mes",
    conexion: sqlite3.Connection = Depends(conexion_api),
):
    """Cuadro de estacionalidad del papel, por mes o por día de la semana.

    El default es USD: en pesos la inflación pinta de verde los doce meses.
    """
    ticker = ticker.upper()
    if ticker not in universo_completo(conexion):
        raise HTTPException(422, f"Ticker desconocido: {ticker}")
    if moneda not in MONEDAS:
        raise HTTPException(422, f"Moneda inválida: {moneda}")
    if vista not in VISTAS:
        raise HTTPException(422, f"Vista inválida: {vista} (usar mes o dia_semana)")
    return VISTAS[vista](conexion, ticker, moneda)
