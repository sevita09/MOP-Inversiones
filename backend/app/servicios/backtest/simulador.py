"""Simulador event-driven, honesto (sin lookahead).

La señal de una barra se conoce recién a su cierre, así que la orden se ejecuta
en la **apertura de la barra siguiente** — nunca en la misma barra que la
generó. Una sola posición a la vez (la metodología es 1 papel por bot).

El Buy & Hold de comparación es el MISMO simulador con las mismas entradas pero
sin salidas y con el 100% del capital: aísla cuánto aporta la salida de la
estrategia ("la entrada define si ganás; la salida, cuánto").
"""
from __future__ import annotations

import sqlite3
from typing import Optional

from app.servicios.backtest.cargador import cargar_historia, recortar
from app.servicios.backtest.metricas import calcular_metricas
from app.servicios.bots.evaluador import evaluar_reglas


def _cerrar_trade(entrada: dict, ts_salida: int, precio_salida: float, abierto: bool) -> dict:
    pnl_pct = (precio_salida / entrada["precio"] - 1) * 100
    return {
        "entrada_ts": entrada["ts"],
        "entrada_precio": round(entrada["precio"], 4),
        "salida_ts": ts_salida,
        "salida_precio": round(precio_salida, 4),
        "pnl_pct": round(pnl_pct, 4),
        "duracion_dias": round((ts_salida - entrada["ts"]) / 86400, 2),
        "gana": pnl_pct > 0,
        "abierto_al_final": abierto,  # se cerró al cierre de la última barra, no por regla
    }


def simular(
    barras: list[dict],
    ts_entrada: set,
    ts_salida: set,
    capital_inicial: float,
    fraccion: float,
) -> dict:
    """Corre la simulación sobre `barras`. Devuelve trades, curva y capital final.

    `fraccion` es la porción del capital que compromete cada entrada (0-1).
    """
    efectivo = capital_inicial
    unidades = 0.0
    entrada_actual: Optional[dict] = None
    pendiente: Optional[str] = None  # 'entrar' | 'salir': señal de la barra previa
    trades: list[dict] = []
    curva: list[dict] = []
    barras_en_posicion = 0

    for barra in barras:
        # 1) Ejecutar en ESTA apertura lo que señaló la barra anterior
        if pendiente == "entrar" and unidades == 0:
            inversion = efectivo * fraccion
            unidades = inversion / barra["apertura"]
            efectivo -= inversion
            entrada_actual = {"ts": barra["ts"], "precio": barra["apertura"]}
        elif pendiente == "salir" and unidades > 0 and entrada_actual:
            efectivo += unidades * barra["apertura"]
            trades.append(_cerrar_trade(entrada_actual, barra["ts"], barra["apertura"], False))
            unidades, entrada_actual = 0.0, None
        pendiente = None

        # 2) Anotar la señal de ESTA barra para ejecutar en la próxima apertura
        if unidades == 0 and barra["ts"] in ts_entrada:
            pendiente = "entrar"
        elif unidades > 0 and barra["ts"] in ts_salida:
            pendiente = "salir"

        # 3) Capital a valor de mercado (al cierre de la barra)
        if unidades > 0:
            barras_en_posicion += 1
        curva.append({"ts": barra["ts"], "capital": round(efectivo + unidades * barra["cierre"], 2)})

    # Posición abierta al final: se cierra al cierre de la última barra
    if unidades > 0 and entrada_actual:
        ultima = barras[-1]
        efectivo += unidades * ultima["cierre"]
        trades.append(_cerrar_trade(entrada_actual, ultima["ts"], ultima["cierre"], True))

    return {
        "capital_inicial": round(capital_inicial, 2),
        "capital_final": round(efectivo, 2),
        "retorno_pct": round((efectivo / capital_inicial - 1) * 100, 4) if capital_inicial else 0.0,
        "barras": len(barras),
        "barras_en_posicion": barras_en_posicion,
        "trades": trades,
        "curva": curva,
    }


def correr_backtest(
    conexion: sqlite3.Connection,
    bot: dict,
    desde: Optional[int] = None,
    hasta: Optional[int] = None,
) -> dict:
    """Backtest de un bot en un rango: estrategia vs Buy & Hold (mismas entradas)."""
    reglas, velas_por, velas_bot = cargar_historia(conexion, bot)
    barras = recortar(velas_bot, desde, hasta)

    senales = evaluar_reglas(velas_por, reglas, bot["temporalidad"])
    ts_entrada = set(senales["ts_entrada"])
    ts_salida = set(senales["ts_salida"])

    capital = bot["capital"]["inicial"]
    fraccion = bot["capital"]["porcentaje_por_posicion"] / 100

    estrategia = simular(barras, ts_entrada, ts_salida, capital, fraccion)
    # Buy & Hold: mismas entradas, sin salidas, 100% del capital
    buy_and_hold = simular(barras, ts_entrada, set(), capital, 1.0)

    estrategia["metricas"] = calcular_metricas(estrategia, bot["temporalidad"])
    buy_and_hold["metricas"] = calcular_metricas(buy_and_hold, bot["temporalidad"])

    return {
        "ticker": bot["ticker"],
        "temporalidad": bot["temporalidad"],
        "moneda": bot["moneda"],
        "desde": barras[0]["ts"] if barras else None,
        "hasta": barras[-1]["ts"] if barras else None,
        "estrategia": estrategia,
        "buy_and_hold": buy_and_hold,
    }
