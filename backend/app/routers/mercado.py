from __future__ import annotations

import sqlite3
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException

from app.config import (
    CEDEARS,
    PANEL_GENERAL,
    PANEL_LIDER,
    TEMPORALIDADES,
    TICKERS_DOLAR,
    todos_los_tickers,
)
from app.db import conexion_api
from app.repositorios.tickers_extra import listar as listar_tickers_extra
from app.repositorios.velas import obtener_velas
from app.servicios.dolar import convertir_velas_a_usd
from app.servicios.precios import calcular_precios

MONEDAS = ("ARS", "USD")


def _tickers_validos(conexion: sqlite3.Connection) -> set:
    extras = {e["ticker"] for e in listar_tickers_extra(conexion)}
    return set(todos_los_tickers()) | set(TICKERS_DOLAR) | extras

router = APIRouter(prefix="/api")


@router.get("/tickers")
def tickers(conexion: sqlite3.Connection = Depends(conexion_api)):
    """Grupos del sidebar: los fijos de config + los agregados por el usuario."""
    extras: dict[str, list[str]] = {}
    for e in listar_tickers_extra(conexion):
        extras.setdefault(e["grupo"], []).append(e["ticker"])
    return {
        "panel_lider": PANEL_LIDER + extras.get("panel_lider", []),
        "panel_general": PANEL_GENERAL + extras.get("panel_general", []),
        "cedears": CEDEARS + extras.get("cedears", []),
        "indices": extras.get("indices", []),
        "cripto": extras.get("cripto", []),
        "dolar": TICKERS_DOLAR + extras.get("dolar", []),
    }


@router.get("/precios")
def precios(
    moneda: str = "ARS",
    conexion: sqlite3.Connection = Depends(conexion_api),
):
    if moneda not in MONEDAS:
        raise HTTPException(422, f"Moneda inválida: {moneda} (usar ARS o USD)")
    todos = list(_tickers_validos(conexion))
    return calcular_precios(conexion, todos, moneda)


@router.get("/velas")
def velas(
    ticker: str,
    temporalidad: str = "D",
    moneda: str = "ARS",
    desde: Optional[int] = None,
    hasta: Optional[int] = None,
    conexion: sqlite3.Connection = Depends(conexion_api),
):
    if temporalidad not in TEMPORALIDADES:
        raise HTTPException(422, f"Temporalidad inválida: {temporalidad} (usar H, D, S o M)")
    if moneda not in MONEDAS:
        raise HTTPException(422, f"Moneda inválida: {moneda} (usar ARS o USD)")
    if ticker not in _tickers_validos(conexion):
        raise HTTPException(404, f"Ticker desconocido: {ticker}")
    velas = obtener_velas(conexion, ticker, temporalidad, desde, hasta)
    if moneda == "USD":
        velas = convertir_velas_a_usd(conexion, ticker, velas)
    return {
        "ticker": ticker,
        "temporalidad": temporalidad,
        "moneda": moneda,
        "velas": velas,
    }
