"""Cálculo y sincronización de las tasas del dólar.

CCL (Contado con Liquidación): se calcula a partir de GGAL en BYMA (ARS) y su
ADR en NYSE (USD). Cada ADR equivale a 10 acciones locales.

    CCL = (GGAL_ars * 10) / GGAL_adr_usd
"""
from __future__ import annotations

import sqlite3
from datetime import datetime, timezone

from app.config import TICKER_CCL_BASE
from app.repositorios.tasas_dolar import CCL, guardar_tasas
from app.repositorios.velas import obtener_velas

# Cada ADR de GGAL en NYSE representa 10 acciones locales
ACCIONES_POR_ADR = 10


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
