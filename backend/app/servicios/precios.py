"""Precio actual y variación diaria por ticker, para la watchlist."""
from __future__ import annotations

import sqlite3
from typing import Optional

from app.config import tickers_byma
from app.repositorios.tickers_extra import listar as listar_tickers_extra
from app.repositorios.velas import obtener_ultimas_velas
from app.servicios.dolar import serie_ccl, tasa_ccl_para_ts


def _tickers_convertibles(conexion: sqlite3.Connection) -> set:
    """Los que cotizan en ARS: BYMA de config + agregados con símbolo .BA."""
    extras = {
        e["ticker"]
        for e in listar_tickers_extra(conexion)
        if e["simbolo_yf"].endswith(".BA")
    }
    return set(tickers_byma()) | extras


def _cierre_en_moneda(
    vela: dict,
    ticker: str,
    moneda: str,
    fechas: list[str],
    valores: list[float],
    convertibles: set,
) -> Optional[float]:
    """Cierre de la vela en la moneda pedida (None si falta la tasa para USD)."""
    if moneda == "ARS" or ticker not in convertibles:
        return vela["cierre"]
    tasa = tasa_ccl_para_ts(fechas, valores, vela["ts"])
    return vela["cierre"] / tasa if tasa else None


def precio_de_ticker(
    conexion: sqlite3.Connection,
    ticker: str,
    moneda: str,
    fechas: list[str],
    valores: list[float],
    convertibles: Optional[set] = None,
) -> Optional[dict]:
    """Último cierre y variación % contra el cierre anterior, en la moneda pedida."""
    if convertibles is None:
        convertibles = _tickers_convertibles(conexion)
    velas = obtener_ultimas_velas(conexion, ticker, "D", 2)
    if not velas:
        return None
    cierre = _cierre_en_moneda(velas[-1], ticker, moneda, fechas, valores, convertibles)
    if cierre is None:
        return None
    variacion = None
    if len(velas) == 2:
        previo = _cierre_en_moneda(velas[0], ticker, moneda, fechas, valores, convertibles)
        if previo:
            variacion = round((cierre - previo) / previo * 100, 2)
    return {"cierre": round(cierre, 4), "variacion_pct": variacion}


def calcular_precios(
    conexion: sqlite3.Connection, tickers: list[str], moneda: str
) -> dict:
    """Precio y variación de cada ticker. Carga la serie CCL una sola vez."""
    fechas, valores = serie_ccl(conexion)
    convertibles = _tickers_convertibles(conexion)
    precios = {}
    for ticker in tickers:
        dato = precio_de_ticker(conexion, ticker, moneda, fechas, valores, convertibles)
        if dato is not None:
            precios[ticker] = dato
    return precios
