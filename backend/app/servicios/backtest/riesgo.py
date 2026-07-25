"""Gestión de riesgo del simulador: stops, take profit, trailing y sizing.

Regla conservadora del backtest: si en una misma barra el precio pudo tocar el
stop Y el take profit, se asume que **tocó el stop primero** (no hay dato
intra-barra del orden real, así que se elige el peor caso). Los gaps se llenan
en la apertura: si la barra abrió más allá del nivel, ese es el precio de salida.
"""
from __future__ import annotations

from typing import Optional


def _stop_inicial(entrada: float, riesgo: dict, atr_entrada: Optional[float]) -> Optional[float]:
    """El stop más protector (más alto) entre el fijo y el de ATR; None si no hay."""
    candidatos = []
    if riesgo.get("stop_loss_pct"):
        candidatos.append(entrada * (1 - riesgo["stop_loss_pct"] / 100))
    if riesgo.get("stop_atr_mult") and atr_entrada:
        candidatos.append(entrada - riesgo["stop_atr_mult"] * atr_entrada)
    return max(candidatos) if candidatos else None


def niveles_iniciales(
    entrada: float, riesgo: dict, atr_entrada: Optional[float]
) -> tuple[Optional[float], Optional[float]]:
    """(stop, take_profit) al abrir la posición."""
    stop = _stop_inicial(entrada, riesgo, atr_entrada)
    tp = entrada * (1 + riesgo["take_profit_pct"] / 100) if riesgo.get("take_profit_pct") else None
    return stop, tp


def actualizar_trailing(stop: Optional[float], riesgo: dict, max_precio: float) -> Optional[float]:
    """Sube el stop con el trailing (nunca lo baja)."""
    if not riesgo.get("trailing_pct"):
        return stop
    trailing = max_precio * (1 - riesgo["trailing_pct"] / 100)
    return trailing if stop is None else max(stop, trailing)


def stop_es_trailing(stop: Optional[float], riesgo: dict, max_precio: float) -> bool:
    """True si el stop vigente es el del trailing (y no el inicial): sirve para
    contar en los resultados por qué motivo se cerró la posición."""
    if not riesgo.get("trailing_pct") or stop is None:
        return False
    trailing = max_precio * (1 - riesgo["trailing_pct"] / 100)
    return abs(stop - trailing) < 1e-9


def salida_intrabarra(
    barra: dict, stop: Optional[float], tp: Optional[float]
) -> tuple[Optional[float], Optional[str]]:
    """Precio y motivo de salida dentro de la barra; el stop tiene prioridad."""
    if stop is not None and barra["minimo"] <= stop:
        # Gap a la baja: si abrió por debajo del stop, se ejecuta en la apertura
        return (min(barra["apertura"], stop), "stop")
    if tp is not None and barra["maximo"] >= tp:
        return (max(barra["apertura"], tp), "take_profit")
    return (None, None)


def unidades_a_comprar(
    efectivo: float, fraccion: float, entrada: float, stop: Optional[float], riesgo: dict
) -> float:
    """Tamaño de la posición.

    Por riesgo (si `sizing_riesgo_pct` está y hay stop): compra tantas unidades
    como para perder ese % del capital si el precio llega al stop. Nunca apalanca
    (se topa con el efectivo disponible). Si no, usa la fracción fija del capital.
    """
    if riesgo.get("sizing_riesgo_pct") and stop is not None and entrada > stop:
        riesgo_monto = efectivo * riesgo["sizing_riesgo_pct"] / 100
        unidades = riesgo_monto / (entrada - stop)
        if unidades * entrada > efectivo:  # no apalancar
            unidades = efectivo / entrada
        return unidades
    return efectivo * fraccion / entrada
