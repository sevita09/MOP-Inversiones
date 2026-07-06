"""Alta de tickers nuevos por el usuario, con validación contra Yahoo Finance.

El usuario elige a qué grupo del sidebar va el ticker, y el grupo define cómo
se resuelve el símbolo en Yahoo:

- panel_lider / panel_general → acción BYMA: `TICKER.BA` (cotiza en ARS)
- cedears → el subyacente del exterior: símbolo crudo en USD (igual que AAPL)
- indices → crudo o con `^` (p.ej. MERV → ^MERV)
- cripto → crudo o par contra USD (p.ej. BTC → BTC-USD)
- dolar → símbolo crudo

El ticker agregado entra al circuito normal: sync de historia, precios, velas,
logo y categorías.
"""
from __future__ import annotations

import sqlite3
from typing import Optional

from app.config import TICKERS_DOLAR, todos_los_tickers
from app.repositorios import tickers_extra as repo

GRUPOS_VALIDOS = ("panel_lider", "panel_general", "cedears", "indices", "cripto", "dolar")


def universo_completo(conexion: sqlite3.Connection) -> set:
    """Todos los tickers válidos: config + dólares + agregados por el usuario."""
    extras = {e["ticker"] for e in repo.listar(conexion)}
    return set(todos_los_tickers()) | set(TICKERS_DOLAR) | extras


def probar_simbolo(simbolo: str) -> bool:
    """True si el símbolo existe en Yahoo Finance (trae historia reciente)."""
    import yfinance as yf  # import acá: los tests no deben cargar yfinance

    try:
        historia = yf.Ticker(simbolo).history(period="5d", raise_errors=False)
    except Exception:
        return False
    return historia is not None and not historia.empty


def candidatos_yahoo(ticker: str, grupo: str) -> list[str]:
    """Símbolos de Yahoo a probar, en orden, según el grupo elegido."""
    if grupo in ("panel_lider", "panel_general"):
        return [f"{ticker}.BA"]
    if grupo == "indices":
        return [ticker] if ticker.startswith("^") else [ticker, f"^{ticker}"]
    if grupo == "cripto":
        return [ticker] if "-" in ticker else [f"{ticker}-USD", ticker]
    return [ticker]  # cedears (subyacente USD) y dolar


def resolver_simbolo(ticker: str, grupo: str) -> Optional[str]:
    for candidato in candidatos_yahoo(ticker, grupo):
        if probar_simbolo(candidato):
            return candidato
    return None


def agregar_ticker(conexion: sqlite3.Connection, ticker: str, grupo: str) -> dict:
    """Valida y agrega el ticker. Lanza ValueError con el motivo si no se puede."""
    ticker = ticker.strip().upper()
    if not ticker:
        raise ValueError("El ticker no puede estar vacío")
    if grupo not in GRUPOS_VALIDOS:
        raise ValueError(f"Grupo inválido: {grupo} (usar {', '.join(GRUPOS_VALIDOS)})")
    if ticker in todos_los_tickers() + TICKERS_DOLAR:
        raise ValueError(f"{ticker} ya está en la app")
    if repo.simbolo_de(conexion, ticker) is not None:
        raise ValueError(f"{ticker} ya fue agregado")

    simbolo = resolver_simbolo(ticker, grupo)
    if simbolo is None:
        raise ValueError(f"{ticker} no se encontró en Yahoo Finance")

    repo.agregar(conexion, ticker, simbolo, grupo)
    return {"ticker": ticker, "simbolo_yf": simbolo, "grupo": grupo}
