from __future__ import annotations

import math
from datetime import datetime, timezone
from typing import Optional

import yfinance as yf

from app.config import (
    HISTORIA_POR_TEMPORALIDAD,
    INTERVALO_YFINANCE,
    TICKER_CCL_BASE,
    tickers_byma,
)


def simbolo_yahoo(ticker: str) -> str:
    """Convierte el ticker propio al símbolo de Yahoo Finance.

    Los BYMA llevan sufijo .BA; GGALD es el ADR de GGAL en NYSE (sin sufijo).
    """
    if ticker == TICKER_CCL_BASE:
        return "GGAL"
    if ticker in tickers_byma():
        return f"{ticker}.BA"
    return ticker


def descargar_velas(
    ticker: str,
    temporalidad: str,
    desde: Optional[int] = None,
) -> list[dict]:
    """Baja velas de yfinance y las devuelve listas para guardar_velas.

    Con `desde` (ts unix) baja solo el delta; sin él, toda la historia configurada.
    """
    historia = yf.Ticker(simbolo_yahoo(ticker)).history(
        interval=INTERVALO_YFINANCE[temporalidad],
        auto_adjust=False,
        **(
            {"start": datetime.fromtimestamp(desde, tz=timezone.utc)}
            if desde is not None
            else {"period": HISTORIA_POR_TEMPORALIDAD[temporalidad]}
        ),
    )
    return convertir_historia(historia, ticker, temporalidad)


def convertir_historia(historia, ticker: str, temporalidad: str) -> list[dict]:
    """Convierte el DataFrame de yfinance a dicts de velas, filtrando inválidas."""
    velas = []
    for indice, fila in historia.iterrows():
        precios = [fila["Open"], fila["High"], fila["Low"], fila["Close"]]
        if any(math.isnan(precio) or precio <= 0 for precio in precios):
            continue
        volumen = fila.get("Volume", 0.0)
        velas.append(
            {
                "ticker": ticker,
                "temporalidad": temporalidad,
                "ts": int(indice.timestamp()),
                "apertura": float(fila["Open"]),
                "maximo": float(fila["High"]),
                "minimo": float(fila["Low"]),
                "cierre": float(fila["Close"]),
                "volumen": 0.0 if math.isnan(volumen) else float(volumen),
            }
        )
    return velas
