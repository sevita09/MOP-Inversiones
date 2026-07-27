from __future__ import annotations

import sqlite3
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException

from app.config import TICKERS_DOLAR
from app.db import conexion_api
from app.esquemas.bots import (
    BacktestRapidoPeticion,
    BotEdicion,
    BotPeticion,
    PreviewPeticion,
)
from app.repositorios import bots as repo
from app.repositorios import senales as repo_senales
from app.servicios.backtest.simulador import correr_backtest
from app.servicios.bots.evaluador import evaluar_reglas, temporalidades_de
from app.servicios.dolar import velas_para_vista
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


@router.post("/bots/preview")
def preview_de_reglas(
    body: PreviewPeticion, conexion: sqlite3.Connection = Depends(conexion_api)
):
    """Evalúa las reglas sobre la historia del ticker (las mismas velas e
    indicadores que ve el chart) y devuelve los ts donde disparan."""
    ticker = _validar_ticker(conexion, body.ticker)
    velas_por = {
        tf: velas_para_vista(conexion, ticker, tf, body.moneda)
        for tf in temporalidades_de(body.reglas, body.temporalidad)
    }
    try:
        return evaluar_reglas(velas_por, body.reglas, body.temporalidad)
    except ValueError as error:
        # Condición de temporalidad menor a la del bot (p.ej. D en un bot S)
        raise HTTPException(422, str(error))


@router.post("/bots/backtest_rapido")
def backtest_rapido(
    body: BacktestRapidoPeticion, conexion: sqlite3.Connection = Depends(conexion_api)
):
    """Backtest de los últimos `meses` sobre una config sin guardar (el editor)."""
    ticker = _validar_ticker(conexion, body.ticker)
    if not body.reglas.entrada:
        raise HTTPException(422, "Sin reglas de entrada no hay nada que backtestear")
    desde = int((datetime.now(timezone.utc) - timedelta(days=body.meses * 30.44)).timestamp())
    bot = {
        "ticker": ticker,
        "temporalidad": body.temporalidad,
        "moneda": body.moneda,
        "capital": body.capital.model_dump(),
        "riesgo": body.riesgo.model_dump(),
        "reglas": body.reglas.model_dump(exclude_none=True),
    }
    try:
        return correr_backtest(conexion, bot, desde, None)
    except ValueError as error:
        raise HTTPException(422, str(error))


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
        body.reglas.model_dump(exclude_none=True) if body.reglas else None,
        body.riesgo.model_dump(),
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
    repo_senales.borrar_de_bot(conexion, id_bot)  # sus señales se van con él
    return {"ok": True}


@router.post("/bots/{id_bot}/duplicar", status_code=201)
def duplicar_bot(id_bot: int, conexion: sqlite3.Connection = Depends(conexion_api)):
    copia = repo.duplicar(conexion, id_bot)
    if copia is None:
        raise HTTPException(404, "Bot no encontrado")
    return copia


@router.get("/bots/{id_bot}/backtest")
def backtest_de_bot(
    id_bot: int,
    desde: Optional[int] = None,
    hasta: Optional[int] = None,
    conexion: sqlite3.Connection = Depends(conexion_api),
):
    """Backtest del bot en un rango (ts unix): estrategia vs Buy & Hold."""
    bot = repo.obtener(conexion, id_bot)
    if bot is None:
        raise HTTPException(404, "Bot no encontrado")
    if not bot["reglas"].get("entrada"):
        raise HTTPException(422, "El bot no tiene reglas de entrada para backtestear")
    resultado = correr_backtest(conexion, bot, desde, hasta)
    # Cachear en el bot un resumen liviano (sin curva ni trades) para la lista
    repo.guardar_metricas(
        conexion,
        id_bot,
        {
            "desde": resultado["desde"],
            "hasta": resultado["hasta"],
            "estrategia": resultado["estrategia"]["metricas"],
            "buy_and_hold_retorno_pct": resultado["buy_and_hold"]["metricas"]["retorno_pct"],
        },
    )
    return resultado
