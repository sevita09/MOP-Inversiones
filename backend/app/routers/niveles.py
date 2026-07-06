from __future__ import annotations

import sqlite3

from fastapi import APIRouter, Depends, HTTPException

from app.config import TEMPORALIDADES
from app.db import conexion_api
from app.repositorios.velas import obtener_velas
from app.servicios.dolar import convertir_velas_a_usd
from app.servicios.tickers_extra import universo_completo
from app.servicios.niveles_swing import SUPERIORES, combinar

router = APIRouter(prefix="/api")

MONEDAS = ("ARS", "USD")


@router.get("/niveles_swing")
def niveles_swing(
    ticker: str,
    temporalidad: str = "D",
    moneda: str = "ARS",
    conexion: sqlite3.Connection = Depends(conexion_api),
):
    if temporalidad not in TEMPORALIDADES:
        raise HTTPException(422, f"Temporalidad inválida: {temporalidad} (usar H, D, S o M)")
    if moneda not in MONEDAS:
        raise HTTPException(422, f"Moneda inválida: {moneda} (usar ARS o USD)")
    if ticker not in universo_completo(conexion):
        raise HTTPException(404, f"Ticker desconocido: {ticker}")

    # La vista más las temporalidades superiores que se le superponen
    temporalidades = [temporalidad] + SUPERIORES.get(temporalidad, [])
    velas_por: dict[str, list[dict]] = {}
    for t in temporalidades:
        velas = obtener_velas(conexion, ticker, t)
        if moneda == "USD":
            velas = convertir_velas_a_usd(conexion, ticker, velas)
        velas_por[t] = velas

    return {
        "ticker": ticker,
        "temporalidad": temporalidad,
        "moneda": moneda,
        "niveles": combinar(velas_por, temporalidad),
    }
