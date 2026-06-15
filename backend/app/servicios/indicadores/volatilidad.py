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


def atr(df: pd.DataFrame, periodo: int = 14) -> dict[str, pd.Series]:
    """Average True Range: la volatilidad media del período (suavizado RMA de Wilder)."""
    alto_bajo = df["maximo"] - df["minimo"]
    alto_cierre = (df["maximo"] - df["cierre"].shift(1)).abs()
    bajo_cierre = (df["minimo"] - df["cierre"].shift(1)).abs()
    tr = pd.concat([alto_bajo, alto_cierre, bajo_cierre], axis=1).max(axis=1)
    return {"atr": tr.ewm(alpha=1 / periodo, adjust=False, min_periods=periodo).mean()}


def porcentaje_b(
    df: pd.DataFrame, periodo: int = 20, desvios: float = 2.0
) -> dict[str, pd.Series]:
    """%B de Bollinger: posición del precio dentro de las bandas (0 = inferior, 1 = superior)."""
    media = df["cierre"].rolling(window=periodo).mean()
    sigma = df["cierre"].rolling(window=periodo).std(ddof=0)
    superior = media + desvios * sigma
    inferior = media - desvios * sigma
    ancho = superior - inferior
    b = (df["cierre"] - inferior) / ancho
    return {"porcentaje_b": b}


def adx(df: pd.DataFrame, periodo: int = 14) -> dict[str, pd.Series]:
    """Average Directional Index: fuerza de la tendencia (0-100), sin dirección."""
    alto = df["maximo"]
    bajo = df["minimo"]
    dm_pos = (alto - alto.shift(1)).clip(lower=0)
    dm_neg = (bajo.shift(1) - bajo).clip(lower=0)
    dm_pos[dm_pos <= dm_neg] = 0
    dm_neg[dm_neg <= dm_pos] = 0
    alpha = 1 / periodo
    tr = pd.concat([
        alto - bajo,
        (alto - df["cierre"].shift(1)).abs(),
        (bajo - df["cierre"].shift(1)).abs(),
    ], axis=1).max(axis=1)
    atr_suave = tr.ewm(alpha=alpha, adjust=False, min_periods=periodo).mean()
    di_pos = 100 * dm_pos.ewm(alpha=alpha, adjust=False, min_periods=periodo).mean() / atr_suave
    di_neg = 100 * dm_neg.ewm(alpha=alpha, adjust=False, min_periods=periodo).mean() / atr_suave
    dx = 100 * (di_pos - di_neg).abs() / (di_pos + di_neg)
    return {"adx": dx.ewm(alpha=alpha, adjust=False, min_periods=periodo).mean()}


def percentil_distancia(
    df: pd.DataFrame, periodo: int = 200, ventana: int = 252
) -> dict[str, pd.Series]:
    """Percentil de la distancia actual del precio a la EMA central dentro de una ventana rolling."""
    ema_central = df["cierre"].ewm(span=periodo, adjust=False).mean()
    distancia = df["cierre"] - ema_central
    return {
        "percentil": distancia.rolling(window=ventana).apply(
            lambda v: (v < v.iloc[-1]).sum() / len(v) * 100, raw=False
        )
    }


registrar("bandas", bandas, {"periodo": 200})
registrar("atr", atr, {"periodo": 14})
registrar("porcentaje_b", porcentaje_b, {"periodo": 20, "desvios": 2.0})
registrar("adx", adx, {"periodo": 14})
registrar("percentil_distancia", percentil_distancia, {"periodo": 200, "ventana": 252})
