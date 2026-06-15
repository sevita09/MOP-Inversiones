from __future__ import annotations

import sqlite3

from fastapi import APIRouter, Depends, HTTPException

from app.config import (
    TEMPORALIDADES,
    TICKERS_DOLAR,
    periodo_ema_central,
    todos_los_tickers,
)
from app.db import conexion_api
from app.repositorios.velas import obtener_velas
from app.servicios.dolar import convertir_velas_a_usd
from app.servicios.indicadores import calcular

router = APIRouter(prefix="/api")

MONEDAS = ("ARS", "USD")

# Indicadores cuya ventana es la EMA central de la metodología: el período
# depende de la temporalidad y lo inyecta el router (no es un default fijo)
INDICADORES_EMA_CENTRAL = {"bandas", "percentil_distancia"}


@router.get("/indicadores")
def indicadores(
    ticker: str,
    temporalidad: str = "D",
    moneda: str = "ARS",
    incluir: str = "",
    conexion: sqlite3.Connection = Depends(conexion_api),
):
    if temporalidad not in TEMPORALIDADES:
        raise HTTPException(422, f"Temporalidad inválida: {temporalidad} (usar H, D, S o M)")
    if moneda not in MONEDAS:
        raise HTTPException(422, f"Moneda inválida: {moneda} (usar ARS o USD)")
    if ticker not in set(todos_los_tickers()) | set(TICKERS_DOLAR):
        raise HTTPException(404, f"Ticker desconocido: {ticker}")

    velas = obtener_velas(conexion, ticker, temporalidad)
    if moneda == "USD":
        velas = convertir_velas_a_usd(conexion, ticker, velas)

    nombres = [n.strip() for n in incluir.split(",") if n.strip()]
    resultado: dict[str, dict] = {}
    for nombre in nombres:
        params = {}
        if nombre in INDICADORES_EMA_CENTRAL:
            params["periodo"] = periodo_ema_central(temporalidad)
        try:
            resultado[nombre] = calcular(nombre, velas, **params)
        except KeyError:
            raise HTTPException(422, f"Indicador desconocido: {nombre}")

    return {
        "ticker": ticker,
        "temporalidad": temporalidad,
        "moneda": moneda,
        "ts": [vela["ts"] for vela in velas],
        "indicadores": resultado,
    }
