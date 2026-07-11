from __future__ import annotations

import json
import sqlite3

from fastapi import APIRouter, Depends, HTTPException

from app.config import (
    TEMPORALIDADES,
    periodo_ema_central,
)
from app.db import conexion_api
from app.servicios.dolar import velas_para_vista
from app.servicios.tickers_extra import universo_completo
from app.servicios.indicadores import calcular, defaults_de

router = APIRouter(prefix="/api")

MONEDAS = ("ARS", "USD")

# Indicadores cuya ventana es la EMA central de la metodología: el período
# depende de la temporalidad y lo inyecta el router (no es un default fijo)
INDICADORES_EMA_CENTRAL = {"bandas", "percentil_distancia"}


def _parsear_params(crudo: str) -> dict[str, dict]:
    """Overrides del usuario: JSON `{"bandas": {"periodo": 250}, "rsi": {...}}`."""
    if not crudo:
        return {}
    try:
        datos = json.loads(crudo)
    except json.JSONDecodeError:
        raise HTTPException(422, "params debe ser JSON válido")
    if not isinstance(datos, dict) or not all(isinstance(v, dict) for v in datos.values()):
        raise HTTPException(422, "params debe ser un objeto de parámetros por indicador")
    return datos


def _params_validos(nombre: str, crudos: dict) -> dict:
    """Filtra a los parámetros que el indicador conoce y los coerce a su tipo."""
    if not crudos:
        return {}
    defaults = defaults_de(nombre)  # KeyError si el indicador no existe
    validos: dict = {}
    for clave, valor in crudos.items():
        if clave not in defaults or defaults[clave] is None:
            continue  # ignora parámetros que el indicador no expone
        tipo = type(defaults[clave])
        try:
            validos[clave] = tipo(valor)
        except (TypeError, ValueError):
            raise HTTPException(422, f"Parámetro inválido {nombre}.{clave}: {valor!r}")
    return validos


@router.get("/indicadores")
def indicadores(
    ticker: str,
    temporalidad: str = "D",
    moneda: str = "ARS",
    incluir: str = "",
    params: str = "",
    conexion: sqlite3.Connection = Depends(conexion_api),
):
    if temporalidad not in TEMPORALIDADES:
        raise HTTPException(422, f"Temporalidad inválida: {temporalidad} (usar H, D, S o M)")
    if moneda not in MONEDAS:
        raise HTTPException(422, f"Moneda inválida: {moneda} (usar ARS o USD)")
    if ticker not in universo_completo(conexion):
        raise HTTPException(404, f"Ticker desconocido: {ticker}")

    velas = velas_para_vista(conexion, ticker, temporalidad, moneda)
    overrides = _parsear_params(params)

    nombres = [n.strip() for n in incluir.split(",") if n.strip()]
    resultado: dict[str, dict] = {}
    for nombre in nombres:
        parametros: dict = {}
        # El período de la EMA central se inyecta por temporalidad, pero el
        # override del usuario (si lo hay) gana: deja de ser un valor fijo.
        if nombre in INDICADORES_EMA_CENTRAL:
            parametros["periodo"] = periodo_ema_central(temporalidad)
        try:
            parametros.update(_params_validos(nombre, overrides.get(nombre, {})))
            resultado[nombre] = calcular(nombre, velas, **parametros)
        except KeyError:
            raise HTTPException(422, f"Indicador desconocido: {nombre}")

    return {
        "ticker": ticker,
        "temporalidad": temporalidad,
        "moneda": moneda,
        "ts": [vela["ts"] for vela in velas],
        "indicadores": resultado,
    }
