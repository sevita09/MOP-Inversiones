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

    La σ es la distancia RMS del precio a la EMA: raíz del promedio (rolling) de
    (precio − EMA)², medida ALREDEDOR DE LA EMA (cero), no alrededor de la media
    de la distancia. Es la dispersión correcta para bandas centradas en la EMA:
    así el precio cae dentro de ±2σ ~95% del tiempo. Usar rolling.std() sería un
    error acá — resta el offset de la distancia (la EMA va atrasada) y deja la σ
    demasiado chica, con el precio casi siempre fuera de las bandas.

    El período de la EMA depende de la temporalidad (D=200, S=50, M=12, H=200);
    el router lo inyecta desde EMA_POR_TEMPORALIDAD.
    """
    if std_periodo is None:
        std_periodo = periodo
    media = df["cierre"].ewm(span=periodo, adjust=False).mean()
    distancia = df["cierre"] - media
    sigma = (distancia**2).rolling(window=std_periodo).mean() ** 0.5
    salida = {"media": media}
    for k in DESVIOS_BANDA:
        salida[f"sup{k}"] = media + k * sigma
        salida[f"inf{k}"] = media - k * sigma
    return salida


registrar("bandas", bandas, {"periodo": 200})
