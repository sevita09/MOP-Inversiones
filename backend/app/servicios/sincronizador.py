from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from typing import Optional

from app.config import TEMPORALIDADES, todos_los_tickers
from app.repositorios.registro_sync import obtener_ultima_sync, registrar_sync
from app.repositorios.velas import (
    guardar_velas,
    obtener_ultima_vela,
    obtener_ultimo_ts,
    obtener_velas,
)
from app.servicios.descarga import descargar_velas

# Cuánto puede envejecer el dato antes de volver a sincronizar (segundos)
VIGENCIA_POR_TEMPORALIDAD = {
    "H": 3600,
    "D": 86400,
    "S": 7 * 86400,
    "M": 30 * 86400,
}


def esta_vencido(
    ultima_sync: Optional[str],
    temporalidad: str,
    ahora: Optional[datetime] = None,
) -> bool:
    """Un dato está vencido si nunca se sincronizó o si pasó su vigencia."""
    if ultima_sync is None:
        return True
    ahora = ahora or datetime.now(timezone.utc)
    transcurrido = (ahora - datetime.fromisoformat(ultima_sync)).total_seconds()
    return transcurrido >= VIGENCIA_POR_TEMPORALIDAD[temporalidad]


def sincronizar_ticker(
    conexion: sqlite3.Connection,
    ticker: str,
    temporalidad: str,
    ahora: Optional[datetime] = None,
) -> int:
    """Sincroniza un ticker/temporalidad si está vencido. Devuelve velas guardadas.

    La primera vez baja toda la historia configurada; después solo el delta
    desde la última vela guardada (inclusive, para refrescar la vela en curso).
    """
    ahora = ahora or datetime.now(timezone.utc)
    if not esta_vencido(obtener_ultima_sync(conexion, ticker, temporalidad), temporalidad, ahora):
        return 0

    desde = obtener_ultimo_ts(conexion, ticker, temporalidad)
    velas = descargar_velas(ticker, temporalidad, desde=desde)
    guardadas = guardar_velas(conexion, velas) if velas else 0
    registrar_sync(conexion, ticker, temporalidad, ahora.isoformat())
    return guardadas


def _fin_de_periodo(ts: int, temporalidad: str) -> int:
    """Primer instante del período siguiente al de la vela que arranca en ts."""
    if temporalidad == "S":
        return ts + 7 * 86400
    inicio = datetime.fromtimestamp(ts, tz=timezone.utc)
    if inicio.month == 12:
        fin = inicio.replace(year=inicio.year + 1, month=1, day=1)
    else:
        fin = inicio.replace(month=inicio.month + 1, day=1)
    return int(fin.replace(hour=0, minute=0, second=0, microsecond=0).timestamp())


def refrescar_velas_en_curso(conexion: sqlite3.Connection, ticker: str) -> int:
    """Completa las velas S y M en curso con las diarias cuando D está más al día.

    S y M tienen vigencias largas; entre sync y sync, su última vela queda con el
    cierre viejo. Si la diaria se sincronizó después, el cierre pasa a ser el último
    cierre diario del período (y los extremos y el volumen se recalculan con las
    diarias). El próximo sync real de S/M pisa la vela con el dato de yfinance.
    """
    sync_diaria = obtener_ultima_sync(conexion, ticker, "D")
    if sync_diaria is None:
        return 0

    refrescadas = 0
    for temporalidad in ("S", "M"):
        sync_propia = obtener_ultima_sync(conexion, ticker, temporalidad)
        if sync_propia is None or sync_propia >= sync_diaria:
            continue
        vela = obtener_ultima_vela(conexion, ticker, temporalidad)
        if vela is None:
            continue
        diarias = obtener_velas(
            conexion,
            ticker,
            "D",
            desde=vela["ts"],
            hasta=_fin_de_periodo(vela["ts"], temporalidad) - 1,
        )
        if not diarias:
            continue
        actualizada = dict(
            vela,
            cierre=diarias[-1]["cierre"],
            maximo=max([vela["maximo"]] + [d["maximo"] for d in diarias]),
            minimo=min([vela["minimo"]] + [d["minimo"] for d in diarias]),
            volumen=sum(d["volumen"] for d in diarias),
        )
        if actualizada != vela:
            guardar_velas(conexion, [actualizada])
            refrescadas += 1
    return refrescadas


def sincronizar_todo(
    conexion: sqlite3.Connection, ahora: Optional[datetime] = None
) -> dict:
    """Recorre todos los tickers y temporalidades. Devuelve el resumen del sync."""
    resumen = {
        "velas_guardadas": 0,
        "pares_sincronizados": 0,
        "velas_refrescadas": 0,
        "errores": [],
    }
    for ticker in todos_los_tickers():
        for temporalidad in TEMPORALIDADES:
            try:
                guardadas = sincronizar_ticker(conexion, ticker, temporalidad, ahora)
            except Exception as error:
                resumen["errores"].append(f"{ticker}/{temporalidad}: {error}")
                continue
            if guardadas:
                resumen["velas_guardadas"] += guardadas
                resumen["pares_sincronizados"] += 1
        resumen["velas_refrescadas"] += refrescar_velas_en_curso(conexion, ticker)
    return resumen
