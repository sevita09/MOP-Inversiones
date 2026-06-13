"""Reparación de velas faltantes o corruptas.

Pipeline (se completa a lo largo de la feature):
1. Marcar velas con precios en cero como faltantes.
2. Detectar huecos de fechas y crear placeholders.
3. Redescarga dirigida del período exacto faltante.
4. Interpolar lo que siga faltando, manteniendo el flag para reintentar.
"""
from __future__ import annotations

import sqlite3

from app.config import tickers_byma, todos_los_tickers
from app.repositorios.velas import (
    guardar_velas,
    marcar_velas_en_cero,
    obtener_calendario,
    obtener_velas,
)


def marcar_corruptas(conexion: sqlite3.Connection) -> int:
    """Marca con es_faltante=1 las velas con precios inválidos. Devuelve cuántas."""
    return marcar_velas_en_cero(conexion)


def companeros_de_mercado(ticker: str) -> list:
    """Los demás tickers del mismo mercado, cuyo calendario de ruedas es compartido."""
    byma = tickers_byma()
    grupo = byma if ticker in byma else [t for t in todos_los_tickers() if t not in byma]
    return [t for t in grupo if t != ticker]


def detectar_huecos(
    conexion: sqlite3.Connection, ticker: str, temporalidad: str
) -> list:
    """Timestamps donde el mercado operó pero el ticker no tiene vela.

    Solo entre la primera y la última vela del ticker: no inventa historia
    anterior a su listado ni posterior a su último dato.
    """
    velas = obtener_velas(conexion, ticker, temporalidad)
    if not velas:
        return []
    existentes = {vela["ts"] for vela in velas}
    calendario = obtener_calendario(
        conexion,
        companeros_de_mercado(ticker),
        temporalidad,
        velas[0]["ts"],
        velas[-1]["ts"],
    )
    return [ts for ts in calendario if ts not in existentes]


def crear_placeholders(
    conexion: sqlite3.Connection, ticker: str, temporalidad: str
) -> int:
    """Crea velas vacías (es_faltante=1) en los huecos detectados. Devuelve cuántas."""
    placeholders = [
        {
            "ticker": ticker,
            "temporalidad": temporalidad,
            "ts": ts,
            "apertura": 0.0,
            "maximo": 0.0,
            "minimo": 0.0,
            "cierre": 0.0,
            "volumen": 0.0,
            "es_faltante": 1,
        }
        for ts in detectar_huecos(conexion, ticker, temporalidad)
    ]
    if placeholders:
        guardar_velas(conexion, placeholders)
    return len(placeholders)
