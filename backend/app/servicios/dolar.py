"""Cálculo y sincronización de las tasas del dólar.

CCL (Contado con Liquidación): se calcula a partir de GGAL en BYMA (ARS) y su
ADR en NYSE (USD). Cada ADR equivale a 10 acciones locales.

    CCL = (GGAL_ars * 10) / GGAL_adr_usd
"""
from __future__ import annotations

import sqlite3
from datetime import datetime, timezone

from app.config import TICKER_CCL_BASE
from app.repositorios.tasas_dolar import CCL, OFICIAL, guardar_tasas, obtener_tasas
from app.repositorios.velas import guardar_velas, obtener_velas
from app.servicios.descarga import descargar_velas

# Cada ADR de GGAL en NYSE representa 10 acciones locales
ACCIONES_POR_ADR = 10

TICKER_CCL = "DOLARCCL"
TICKER_OFICIAL = "DOLAROF"


def _fecha_a_ts(fecha: str) -> int:
    return int(datetime.strptime(fecha, "%Y-%m-%d").replace(tzinfo=timezone.utc).timestamp())


def _por_fecha(velas: list[dict]) -> dict[str, dict]:
    """Indexa velas diarias por fecha AAAA-MM-DD (UTC)."""
    indexado = {}
    for vela in velas:
        fecha = datetime.fromtimestamp(vela["ts"], tz=timezone.utc).strftime("%Y-%m-%d")
        indexado[fecha] = vela
    return indexado


def calcular_ccl_diario(
    velas_ars: list[dict], velas_adr: list[dict]
) -> list[dict]:
    """Combina las series diarias de GGAL (ARS) y su ADR (USD) en tasas CCL.

    Solo emite tasa en las fechas donde hay vela real (no faltante) de ambos
    lados, con cierres positivos.
    """
    adr_por_fecha = _por_fecha(velas_adr)
    tasas = []
    for fecha, vela_ars in _por_fecha(velas_ars).items():
        vela_adr = adr_por_fecha.get(fecha)
        if vela_adr is None:
            continue
        if vela_ars.get("es_faltante") or vela_adr.get("es_faltante"):
            continue
        cierre_ars, cierre_adr = vela_ars["cierre"], vela_adr["cierre"]
        if cierre_ars <= 0 or cierre_adr <= 0:
            continue
        tasas.append(
            {
                "fecha": fecha,
                "tipo": CCL,
                "valor": round(cierre_ars * ACCIONES_POR_ADR / cierre_adr, 4),
            }
        )
    return sorted(tasas, key=lambda t: t["fecha"])


def sincronizar_ccl(conexion: sqlite3.Connection) -> int:
    """Recalcula la serie CCL desde las velas diarias guardadas. Devuelve cuántas."""
    velas_ars = obtener_velas(conexion, "GGAL", "D")
    velas_adr = obtener_velas(conexion, TICKER_CCL_BASE, "D")
    tasas = calcular_ccl_diario(velas_ars, velas_adr)
    return guardar_tasas(conexion, tasas) if tasas else 0


def _tasa_a_vela(ticker: str, fecha: str, valor: float) -> dict:
    """Una tasa diaria como vela sintética (OHLC = el valor de la tasa)."""
    return {
        "ticker": ticker,
        "temporalidad": "D",
        "ts": _fecha_a_ts(fecha),
        "apertura": valor,
        "maximo": valor,
        "minimo": valor,
        "cierre": valor,
        "volumen": 0.0,
        "es_faltante": 0,
    }


def generar_velas_ccl(conexion: sqlite3.Connection) -> int:
    """Crea velas sintéticas DOLARCCL desde la serie de tasas CCL. Devuelve cuántas."""
    velas = [
        _tasa_a_vela(TICKER_CCL, tasa["fecha"], tasa["valor"])
        for tasa in obtener_tasas(conexion, CCL)
    ]
    return guardar_velas(conexion, velas) if velas else 0


def sincronizar_dolar_oficial(conexion: sqlite3.Connection) -> int:
    """Baja el dólar oficial de yfinance, lo guarda como velas DOLAROF y como tasas.

    Devuelve cuántas velas guardó.
    """
    velas = descargar_velas(TICKER_OFICIAL, "D")
    if not velas:
        return 0
    guardar_velas(conexion, velas)
    tasas = [
        {
            "fecha": datetime.fromtimestamp(vela["ts"], tz=timezone.utc).strftime("%Y-%m-%d"),
            "tipo": OFICIAL,
            "valor": vela["cierre"],
        }
        for vela in velas
    ]
    guardar_tasas(conexion, tasas)
    return len(velas)
