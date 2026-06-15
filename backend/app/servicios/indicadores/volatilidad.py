"""Indicadores de volatilidad."""
from __future__ import annotations

import pandas as pd

from app.servicios.indicadores.registro import registrar

# Desvíos de las bandas alrededor de la EMA central (±1σ, ±2σ, ±3σ)
DESVIOS_BANDA = (1, 2, 3)


def bandas(
    df: pd.DataFrame, periodo: int = 200, std_periodo: int | None = None
) -> dict[str, pd.Series]:
    """EMA central y bandas ±1σ/2σ/3σ — el indicador principal de la metodología.

    La σ es el desvío estándar (rolling) de la distancia precio−EMA sobre la
    ventana, igual que en z_score: mide cuánto se aparta el precio de su media,
    no la volatilidad del retorno. El período de la EMA depende de la
    temporalidad (D=200, S=50, M=12, H=200); el router lo inyecta desde
    EMA_POR_TEMPORALIDAD.
    """
    if std_periodo is None:
        std_periodo = periodo
    media = df["cierre"].ewm(span=periodo, adjust=False).mean()
    distancia = df["cierre"] - media
    std = distancia.rolling(window=std_periodo).std()
    salida = {"media": media}
    for k in DESVIOS_BANDA:
        salida[f"sup{k}"] = media + k * std
        salida[f"inf{k}"] = media - k * std
    return salida


registrar("bandas", bandas, {"periodo": 200})
