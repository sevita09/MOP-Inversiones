"""Métricas honestas de un backtest, a partir de sus trades y su curva de capital.

Se calculan sobre el resultado de `simular` (no recalculan la simulación). El
Sharpe/Sortino se anualizan según la temporalidad del bot (cuántas barras entran
en un año). Con pocos trades o curva plana, las métricas que no tienen sentido
devuelven None en vez de un número engañoso.
"""
from __future__ import annotations

import math

# Barras por año según la temporalidad (para anualizar sharpe/sortino)
BARRAS_POR_ANIO = {"D": 252, "S": 52, "M": 12}


def _drawdown_maximo_pct(curva: list[dict]) -> float:
    """Peor caída pico-a-valle de la curva de capital, en %."""
    pico = None
    peor = 0.0
    for punto in curva:
        capital = punto["capital"]
        if pico is None or capital > pico:
            pico = capital
        if pico:
            caida = (capital - pico) / pico * 100
            peor = min(peor, caida)
    return round(peor, 4)


def _retornos_periodicos(curva: list[dict]) -> list[float]:
    retornos = []
    for previo, actual in zip(curva, curva[1:]):
        if previo["capital"]:
            retornos.append(actual["capital"] / previo["capital"] - 1)
    return retornos


def _sharpe(retornos: list[float], barras_anio: int) -> float | None:
    if len(retornos) < 2:
        return None
    media = sum(retornos) / len(retornos)
    var = sum((r - media) ** 2 for r in retornos) / (len(retornos) - 1)
    desvio = math.sqrt(var)
    if desvio == 0:
        return None
    return round(media / desvio * math.sqrt(barras_anio), 4)


def _sortino(retornos: list[float], barras_anio: int) -> float | None:
    if len(retornos) < 2:
        return None
    media = sum(retornos) / len(retornos)
    # Desvío a la baja: raíz del promedio de los retornos negativos al cuadrado
    bajistas = sum(min(r, 0) ** 2 for r in retornos) / len(retornos)
    desvio_baja = math.sqrt(bajistas)
    if desvio_baja == 0:
        return None
    return round(media / desvio_baja * math.sqrt(barras_anio), 4)


def _racha_maxima_perdidas(trades: list[dict]) -> int:
    peor = 0
    actual = 0
    for trade in trades:
        if trade["gana"]:
            actual = 0
        else:
            actual += 1
            peor = max(peor, actual)
    return peor


def calcular_metricas(simulacion: dict, temporalidad: str) -> dict:
    """Métricas del resultado de una simulación (estrategia o buy & hold)."""
    trades = simulacion["trades"]
    curva = simulacion["curva"]
    barras_anio = BARRAS_POR_ANIO.get(temporalidad, 252)

    total = len(trades)
    ganados = sum(1 for t in trades if t["gana"])
    ganancias = sum(t["pnl_pct"] for t in trades if t["pnl_pct"] > 0)
    perdidas = sum(-t["pnl_pct"] for t in trades if t["pnl_pct"] < 0)
    retornos = _retornos_periodicos(curva)

    barras = simulacion.get("barras", len(curva))
    en_posicion = simulacion.get("barras_en_posicion", 0)

    return {
        "retorno_pct": simulacion["retorno_pct"],
        "trades_total": total,
        "trades_ganados": ganados,
        "win_rate_pct": round(ganados / total * 100, 2) if total else None,
        "drawdown_maximo_pct": _drawdown_maximo_pct(curva),
        "sharpe": _sharpe(retornos, barras_anio),
        "sortino": _sortino(retornos, barras_anio),
        # Ganancia bruta / pérdida bruta (en % por trade). None si no hubo pérdidas
        "profit_factor": round(ganancias / perdidas, 4) if perdidas else None,
        "expectancy_pct": round(sum(t["pnl_pct"] for t in trades) / total, 4) if total else None,
        "exposicion_pct": round(en_posicion / barras * 100, 2) if barras else 0.0,
        "racha_maxima_perdidas": _racha_maxima_perdidas(trades),
    }
