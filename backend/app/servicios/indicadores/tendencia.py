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

    La σ es el desvío estándar (rolling) de la distancia precio−EMA, no de los
    retornos. Es la métrica central de la metodología (señales y confluencia).
    """
    ema_central = df["cierre"].ewm(span=ema_periodo, adjust=False).mean()
    distancia = df["cierre"] - ema_central
    std = distancia.rolling(window=std_periodo).std()
    return {"z": distancia / std}


registrar("ema", ema, {"periodo": 200})
registrar("z_score", z_score, {"ema_periodo": 200, "std_periodo": 200})
