"""Indicadores de tendencia."""
from __future__ import annotations

import pandas as pd

from app.servicios.indicadores.registro import registrar


def ema(df: pd.DataFrame, periodo: int = 200) -> dict[str, pd.Series]:
    """Media móvil exponencial del cierre."""
    return {"ema": df["cierre"].ewm(span=periodo, adjust=False).mean()}


def z_score(
    df: pd.DataFrame, ema_periodo: int = 200, std_periodo: int = 200
) -> dict[str, pd.Series]:
    """Posición normalizada del precio respecto a su EMA: (precio − EMA) / σ.

    La σ es la distancia RMS a la EMA: raíz del promedio (rolling) de
    (precio − EMA)², medida ALREDEDOR DE LA EMA (cero), igual que en las bandas
    (ver `volatilidad.bandas`). Así z = ±k coincide exactamente con la banda
    ±kσ. Es la métrica central de la metodología (señales y confluencia).
    """
    ema_central = df["cierre"].ewm(span=ema_periodo, adjust=False).mean()
    distancia = df["cierre"] - ema_central
    sigma = (distancia**2).rolling(window=std_periodo).mean() ** 0.5
    return {"z": distancia / sigma}


registrar("ema", ema, {"periodo": 200})
registrar("z_score", z_score, {"ema_periodo": 200, "std_periodo": 200})
