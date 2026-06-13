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
    obtener_ts_faltantes,
    obtener_velas,
)
from app.servicios.descarga import descargar_velas

# Duración de una vela por temporalidad, para cerrar el rango de redescarga
PASO_POR_TEMPORALIDAD = {"H": 3600, "D": 86400, "S": 7 * 86400, "M": 31 * 86400}

# Pesos de los vecinos para interpolar (se renormalizan si alguno falta)
PESOS_VECINOS = ((-1, 0.4), (-2, 0.1), (1, 0.4), (2, 0.1))


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


def redescargar_faltantes(
    conexion: sqlite3.Connection, ticker: str, temporalidad: str
) -> int:
    """Reintenta bajar de yfinance exactamente el período de las velas faltantes.

    Las velas que llegan con datos reales pisan el placeholder y limpian el flag
    (guardar_velas las inserta con es_faltante=0). Devuelve cuántas recuperó.
    """
    faltantes = obtener_ts_faltantes(conexion, ticker, temporalidad)
    if not faltantes:
        return 0
    velas = descargar_velas(
        ticker,
        temporalidad,
        desde=faltantes[0],
        hasta=faltantes[-1] + PASO_POR_TEMPORALIDAD[temporalidad],
    )
    pendientes = set(faltantes)
    recuperadas = [vela for vela in velas if vela["ts"] in pendientes]
    if recuperadas:
        guardar_velas(conexion, recuperadas)
    return len(recuperadas)


def interpolar_faltantes(
    conexion: sqlite3.Connection, ticker: str, temporalidad: str
) -> int:
    """Estima las velas faltantes con el promedio ponderado de sus vecinas reales.

    La vela interpolada CONSERVA es_faltante=1: es un valor estimado, y el flag
    hace que la redescarga la reintente en el próximo arranque. Devuelve cuántas
    interpoló (re-interpola las ya estimadas por si una vecina se reparó).
    """
    velas = obtener_velas(conexion, ticker, temporalidad)
    interpoladas = []
    for indice, vela in enumerate(velas):
        if not vela["es_faltante"]:
            continue
        acumulado = {"apertura": 0.0, "maximo": 0.0, "minimo": 0.0, "cierre": 0.0}
        suma_pesos = 0.0
        for desplazamiento, peso in PESOS_VECINOS:
            vecino_indice = indice + desplazamiento
            if not 0 <= vecino_indice < len(velas):
                continue
            vecina = velas[vecino_indice]
            if vecina["es_faltante"]:
                continue
            for campo in acumulado:
                acumulado[campo] += peso * vecina[campo]
            suma_pesos += peso
        if suma_pesos == 0:
            continue  # sin vecinas reales: queda el placeholder en cero
        interpoladas.append(
            dict(
                vela,
                **{campo: round(valor / suma_pesos, 4) for campo, valor in acumulado.items()},
                volumen=0.0,
                es_faltante=1,
            )
        )
    if interpoladas:
        guardar_velas(conexion, interpoladas)
    return len(interpoladas)


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
