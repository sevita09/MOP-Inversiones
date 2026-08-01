from __future__ import annotations

import sqlite3
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException

from app.db import conexion_api
from app.servicios.correlaciones import matriz_correlacion, rolling
from app.servicios.inflacion import TICKER as TICKER_INFLACION
from app.servicios.estacionalidad import por_dia_semana, por_mes
from app.servicios.tickers_extra import universo_completo

router = APIRouter(prefix="/api/analisis")

MONEDAS = ("ARS", "USD")
VISTAS = {"mes": por_mes, "dia_semana": por_dia_semana}
TEMPORALIDADES = ("D", "S", "M")


def _validar(conexion: sqlite3.Connection, tickers: list, moneda: str, temporalidad: str) -> list:
    """Tickers del universo, moneda y temporalidad válidas.

    La inflación no es un papel y no está en el universo, pero sí es una serie
    correlacionable: se admite explícitamente.
    """
    universo = universo_completo(conexion) | {TICKER_INFLACION}
    limpios = [t.strip().upper() for t in tickers if t.strip()]
    desconocidos = [t for t in limpios if t not in universo]
    if desconocidos:
        raise HTTPException(422, f"Tickers desconocidos: {', '.join(desconocidos)}")
    if moneda not in MONEDAS:
        raise HTTPException(422, f"Moneda inválida: {moneda}")
    if temporalidad not in TEMPORALIDADES:
        raise HTTPException(422, f"Temporalidad inválida: {temporalidad} (usar D, S o M)")
    return limpios


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


@router.get("/correlaciones")
def correlaciones(
    tickers: str,
    temporalidad: str = "D",
    moneda: str = "USD",
    desde: Optional[int] = None,
    conexion: sqlite3.Connection = Depends(conexion_api),
):
    """Matriz de correlación entre los papeles pedidos, separados por coma.

    En dólares por defecto: en pesos la devaluación es un factor común que infla
    todas las correlaciones y esconde qué papeles se mueven de verdad juntos.
    """
    lista = _validar(conexion, tickers.split(","), moneda, temporalidad)
    if len(lista) < 2:
        raise HTTPException(422, "Hacen falta al menos dos papeles para correlacionar")
    return matriz_correlacion(conexion, lista, temporalidad, moneda, desde)


@router.get("/correlacion_par")
def correlacion_par(
    a: str,
    b: str,
    temporalidad: str = "D",
    moneda: str = "USD",
    ventana: int = 60,
    desde: Optional[int] = None,
    conexion: sqlite3.Connection = Depends(conexion_api),
):
    """Correlación móvil y dispersión de un par: cómo cambió en el tiempo."""
    lista = _validar(conexion, [a, b], moneda, temporalidad)
    if len(lista) != 2:
        raise HTTPException(422, "Hacen falta dos papeles distintos")
    if not 10 <= ventana <= 5000:
        raise HTTPException(422, "La ventana va de 10 a 5000 períodos")
    return rolling(conexion, lista[0], lista[1], temporalidad, moneda, ventana, desde)
