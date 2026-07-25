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

from app.config import periodo_ema_central
from app.servicios.backtest.cargador import cargar_historia, recortar
from app.servicios.backtest.metricas import calcular_metricas
from app.servicios.backtest.riesgo import (
    actualizar_trailing,
    niveles_iniciales,
    salida_intrabarra,
    stop_es_trailing,
    unidades_a_comprar,
)
from app.servicios.bots.evaluador import evaluar_reglas
from app.servicios.indicadores import calcular


def _cerrar_trade(entrada: dict, ts_salida: int, precio_salida: float, motivo: str) -> dict:
    pnl_pct = (precio_salida / entrada["precio"] - 1) * 100
    return {
        "entrada_ts": entrada["ts"],
        "entrada_precio": round(entrada["precio"], 4),
        "salida_ts": ts_salida,
        "salida_precio": round(precio_salida, 4),
        "pnl_pct": round(pnl_pct, 4),
        "duracion_dias": round((ts_salida - entrada["ts"]) / 86400, 2),
        "gana": pnl_pct > 0,
        "motivo": motivo,  # 'senal' | 'stop' | 'take_profit' | 'fin'
        "abierto_al_final": motivo == "fin",
    }


def simular(
    barras: list[dict],
    ts_entrada: set,
    ts_salida: set,
    capital_inicial: float,
    fraccion: float,
    riesgo: Optional[dict] = None,
    atr_por_ts: Optional[dict] = None,
) -> dict:
    """Corre la simulación sobre `barras`. Devuelve trades, curva y capital final.

    `fraccion` es la porción del capital que compromete cada entrada (0-1).
    `riesgo` agrega stops/take profit/trailing intra-barra y sizing por ATR.
    """
    riesgo = riesgo or {}
    atr_por_ts = atr_por_ts or {}
    efectivo = capital_inicial
    unidades = 0.0
    posicion: Optional[dict] = None  # {ts, precio, stop, tp, max_precio}
    pendiente: Optional[str] = None  # 'entrar' | 'salir': señal de la barra previa
    trades: list[dict] = []
    curva: list[dict] = []
    barras_en_posicion = 0

    for barra in barras:
        # 1) Ejecutar en ESTA apertura lo que señaló la barra anterior
        if pendiente == "entrar" and unidades == 0:
            precio = barra["apertura"]
            stop, tp = niveles_iniciales(precio, riesgo, atr_por_ts.get(barra["ts"]))
            unidades = unidades_a_comprar(efectivo, fraccion, precio, stop, riesgo)
            efectivo -= unidades * precio
            # max_precio arranca en la entrada: el trailing de la barra siguiente
            # se basa en el máximo YA cerrado, no en el de la barra en curso
            posicion = {"ts": barra["ts"], "precio": precio, "stop": stop, "tp": tp, "max_precio": precio}
        elif pendiente == "salir" and unidades > 0 and posicion:
            efectivo += unidades * barra["apertura"]
            trades.append(_cerrar_trade(posicion, barra["ts"], barra["apertura"], "senal"))
            unidades, posicion = 0.0, None
        pendiente = None

        # 2) Riesgo intra-barra: el trailing usa el máximo hasta la barra anterior,
        #    se chequea la salida con esta barra, y recién después se suma su máximo
        #    (evita que el propio máximo de la barra suba un stop que su mínimo gatilla)
        if unidades > 0 and posicion:
            posicion["stop"] = actualizar_trailing(posicion["stop"], riesgo, posicion["max_precio"])
            precio_salida, motivo = salida_intrabarra(barra, posicion["stop"], posicion["tp"])
            # Distinguir el trailing del stop inicial: son gestiones distintas
            if motivo == "stop" and stop_es_trailing(posicion["stop"], riesgo, posicion["max_precio"]):
                motivo = "trailing"
            if precio_salida is not None:
                efectivo += unidades * precio_salida
                trades.append(_cerrar_trade(posicion, barra["ts"], precio_salida, motivo))
                unidades, posicion = 0.0, None
            else:
                posicion["max_precio"] = max(posicion["max_precio"], barra["maximo"])

        # 3) Anotar la señal de ESTA barra para ejecutar en la próxima apertura
        if unidades == 0 and barra["ts"] in ts_entrada:
            pendiente = "entrar"
        elif unidades > 0 and barra["ts"] in ts_salida:
            pendiente = "salir"

        # 4) Capital a valor de mercado (al cierre de la barra)
        if unidades > 0:
            barras_en_posicion += 1
        curva.append({"ts": barra["ts"], "capital": round(efectivo + unidades * barra["cierre"], 2)})

    # Posición abierta al final: se cierra al cierre de la última barra
    if unidades > 0 and posicion:
        ultima = barras[-1]
        efectivo += unidades * ultima["cierre"]
        trades.append(_cerrar_trade(posicion, ultima["ts"], ultima["cierre"], "fin"))

    return {
        "capital_inicial": round(capital_inicial, 2),
        "capital_final": round(efectivo, 2),
        "retorno_pct": round((efectivo / capital_inicial - 1) * 100, 4) if capital_inicial else 0.0,
        "barras": len(barras),
        "barras_en_posicion": barras_en_posicion,
        "trades": trades,
        "curva": curva,
    }


def _atr_por_ts(velas: list[dict], periodo: int) -> dict:
    """ATR disponible en la apertura de cada barra = el de la barra anterior (cerrada)."""
    serie = calcular("atr", velas, periodo=periodo)["atr"]
    return {
        velas[i]["ts"]: serie[i - 1]
        for i in range(1, len(velas))
        if serie[i - 1] is not None
    }


def _cruces_bajo_ema_central(velas: list[dict], temporalidad: str) -> set:
    """ts donde el cierre cruza hacia abajo la EMA central (salida por regla)."""
    media = calcular("bandas", velas, periodo=periodo_ema_central(temporalidad))["media"]
    cruces = set()
    for i in range(1, len(velas)):
        if media[i] is None or media[i - 1] is None:
            continue
        if velas[i - 1]["cierre"] >= media[i - 1] and velas[i]["cierre"] < media[i]:
            cruces.add(velas[i]["ts"])
    return cruces


def correr_backtest(
    conexion: sqlite3.Connection,
    bot: dict,
    desde: Optional[int] = None,
    hasta: Optional[int] = None,
) -> dict:
    """Backtest de un bot en un rango: estrategia vs Buy & Hold (mismas entradas)."""
    reglas, velas_por, velas_bot = cargar_historia(conexion, bot)
    barras = recortar(velas_bot, desde, hasta)
    riesgo = bot.get("riesgo") or {}

    senales = evaluar_reglas(velas_por, reglas, bot["temporalidad"])
    ts_entrada = set(senales["ts_entrada"])
    ts_salida = set(senales["ts_salida"])

    # Salida por regla adicional: el cierre cruza hacia abajo la EMA central
    if riesgo.get("salida_ema_central"):
        ts_salida |= _cruces_bajo_ema_central(velas_bot, bot["temporalidad"])

    # ATR (de la barra anterior, sin lookahead) para stops y sizing por volatilidad
    atr_por_ts = {}
    if riesgo.get("stop_atr_mult") or riesgo.get("sizing_riesgo_pct"):
        atr_por_ts = _atr_por_ts(velas_bot, riesgo.get("atr_periodo", 14))

    capital = bot["capital"]["inicial"]
    fraccion = bot["capital"]["porcentaje_por_posicion"] / 100

    estrategia = simular(barras, ts_entrada, ts_salida, capital, fraccion, riesgo, atr_por_ts)
    # Buy & Hold: mismas entradas, sin salidas ni riesgo, 100% del capital
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
