"""Indicadores de momento."""
from __future__ import annotations

import pandas as pd

from app.servicios.indicadores.registro import registrar


def rsi(df: pd.DataFrame, periodo: int = 14) -> dict[str, pd.Series]:
    """Índice de fuerza relativa con suavizado de Wilder (RMA)."""
    delta = df["cierre"].diff()
    ganancia = delta.clip(lower=0)
    perdida = -delta.clip(upper=0)
    # RMA = ewm con alpha = 1/periodo (suavizado de Wilder)
    prom_ganancia = ganancia.ewm(alpha=1 / periodo, adjust=False, min_periods=periodo).mean()
    prom_perdida = perdida.ewm(alpha=1 / periodo, adjust=False, min_periods=periodo).mean()
    rs = prom_ganancia / prom_perdida
    return {"rsi": 100 - 100 / (1 + rs)}


def macd(
    df: pd.DataFrame, rapida: int = 12, lenta: int = 26, senal: int = 9
) -> dict[str, pd.Series]:
    """MACD: línea (EMA rápida − EMA lenta), su señal y el histograma."""
    ema_rapida = df["cierre"].ewm(span=rapida, adjust=False).mean()
    ema_lenta = df["cierre"].ewm(span=lenta, adjust=False).mean()
    linea = ema_rapida - ema_lenta
    linea_senal = linea.ewm(span=senal, adjust=False).mean()
    return {"macd": linea, "senal": linea_senal, "histograma": linea - linea_senal}


registrar("rsi", rsi, {"periodo": 14})
registrar("macd", macd, {"rapida": 12, "lenta": 26, "senal": 9})
