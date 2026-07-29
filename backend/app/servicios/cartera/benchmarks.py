"""TWR de la cartera y comparación contra el dólar y el mercado.

El **retorno simple** (valor final sobre lo aportado) engaña apenas hay flujos:
si metiste plata justo antes de una suba, el porcentaje se infla sin que hayas
acertado nada. El **TWR** (retorno ponderado por tiempo) parte la historia en
tramos entre flujo y flujo, calcula el rendimiento de cada tramo y los encadena
— así queda el rendimiento de las *decisiones*, que es lo comparable contra un
benchmark.

    r_t = (V_t − F_t) / V_(t−1) − 1        TWR = Π (1 + r_t) − 1

donde `F_t` es la plata que entró (o salió) ese día. Los benchmarks son el
**MEP** (el dólar con el que se valúa la cartera), el **CCL**, el **MERVAL**
(¿le gané al mercado?) y, en la vista en pesos, la **inflación** (¿le gané al
costo de vida?). Todos van a base 100 en la misma rueda inicial que la cartera.
"""
from __future__ import annotations

import sqlite3
from typing import Optional

from app.repositorios.tasas_dolar import CCL, MEP, OFICIAL
from app.servicios.cartera import TIPO_DOLAR
from app.servicios.cartera.curva import serie_de_precios, serie_valor, tasas_alineadas
from app.servicios.inflacion import indice_alineado

TICKER_MERCADO = "MERVAL"

# Papeles que hacen de benchmark, con el ticker del que sale su serie. Los que
# cotizan en dólares se pasan a pesos en la vista en pesos, y al revés.
PAPELES_BENCHMARK = {
    "mercado": TICKER_MERCADO,  # MERVAL
    "spy": "SPY",  # S&P 500
    "qqq": "QQQ",  # Nasdaq 100
    "btc": "BTC",
    "brkb": "BRKB",  # Berkshire: solo tiene sentido medido en dólares
}

TASAS_BENCHMARK = {"oficial": OFICIAL, "mep": MEP, "dolar": CCL}


def retornos_diarios(serie: list[dict]) -> list[float]:
    """Retorno de cada rueda, descontando el flujo de capital de ese día.

    El flujo se toma al cierre: la compra de hoy todavía no tuvo tiempo de
    rendir, así que se resta del valor final antes de comparar contra ayer.
    """
    retornos = []
    for anterior, actual in zip(serie, serie[1:]):
        base = anterior["valor"]
        retornos.append((actual["valor"] - actual["flujo"]) / base - 1 if base > 1e-9 else 0.0)
    return retornos


def twr(serie: list[dict]) -> Optional[float]:
    """Retorno ponderado por tiempo de toda la serie, en porcentaje."""
    if len(serie) < 2:
        return None
    acumulado = 1.0
    for retorno in retornos_diarios(serie):
        acumulado *= 1 + retorno
    return round((acumulado - 1) * 100, 2)


def curva_base_100(serie: list[dict]) -> list[float]:
    """La cartera en base 100: solo rendimiento, sin el ruido de los aportes."""
    valores = [100.0]
    for retorno in retornos_diarios(serie):
        valores.append(valores[-1] * (1 + retorno))
    return [round(v, 2) for v in valores]


def _precios_base_100(precios: list) -> list:
    """Serie de precios normalizada a 100 en su primer dato conocido."""
    inicial = next((p for p in precios if p), None)
    if not inicial:
        return [None] * len(precios)
    return [round(p / inicial * 100, 2) if p else None for p in precios]


def _serie_dolar(
    conexion: sqlite3.Connection, tipo: str, moneda: str, fechas: list
) -> list:
    """Un dólar como referencia: cuánto rendía quedarse en él.

    Las tasas son pesos por dólar. En la vista en dólares hay que medirlas
    contra el dólar de valuación (el MEP): así el MEP queda plano —quedarse en
    dólares no rinde en dólares— y el CCL muestra cuánto se abrió o cerró la
    brecha entre los dos.
    """
    tasas = tasas_alineadas(conexion, tipo, fechas)
    if moneda == "USD":
        valuacion = tasas_alineadas(conexion, TIPO_DOLAR, fechas)
        tasas = [
            tasa / referencia if tasa and referencia else None
            for tasa, referencia in zip(tasas, valuacion)
        ]
    return _precios_base_100(tasas)


def _valor_antes_de(
    conexion: sqlite3.Connection, moneda: str, desde: Optional[str], primera: str
) -> float:
    """Cuánto valía la cartera en la rueda anterior al período.

    Sin recorte no hay nada antes: la serie arranca en la primera operación.
    """
    if not desde:
        return 0.0
    anteriores = [p["valor"] for p in serie_valor(conexion, moneda) if p["fecha"] < primera]
    return anteriores[-1] if anteriores else 0.0


def _variacion(base_100: list) -> Optional[float]:
    ultimo = next((v for v in reversed(base_100) if v is not None), None)
    return round(ultimo - 100, 2) if ultimo is not None else None


def comparacion(
    conexion: sqlite3.Connection, moneda: str = "ARS", desde: Optional[str] = None
) -> dict:
    """Curva de la cartera contra el dólar y el MERVAL, todo en base 100.

    Devuelve también el resumen: el TWR, cuánta plata hay puesta y el resultado
    contra cada benchmark en puntos porcentuales.
    """
    serie = serie_valor(conexion, moneda, desde)
    if not serie:
        return {"fechas": [], "cartera": [], "benchmarks": {}, "totales": {}}

    fechas = [punto["fecha"] for punto in serie]
    cartera = curva_base_100(serie)
    benchmarks = {
        clave: _serie_dolar(conexion, tipo, moneda, fechas)
        for clave, tipo in TASAS_BENCHMARK.items()
    }
    for clave, ticker in PAPELES_BENCHMARK.items():
        # Berkshire es el benchmark "en dólares": en pesos lo reemplaza la inflación
        if clave == "brkb" and moneda == "ARS":
            continue
        benchmarks[clave] = _precios_base_100(
            serie_de_precios(conexion, ticker, moneda, fechas)
        )
    # La inflación es un fenómeno en pesos: medida en dólares no significa nada
    if moneda == "ARS":
        benchmarks["inflacion"] = _precios_base_100(indice_alineado(conexion, fechas))

    rendimiento = twr(serie)
    aportado = round(sum(punto["flujo"] for punto in serie), 2)
    valor_final = serie[-1]["valor"]
    # Ganancia del período: lo que quedó, menos lo que ya valía la cartera al
    # entrar al período, menos lo que se aportó en el medio. Sin restar el valor
    # previo, una ventana corta contaría como ganancia una posición que venía de
    # antes; con la historia completa ese valor previo es cero.
    ganancia = valor_final - _valor_antes_de(conexion, moneda, desde, fechas[0]) - aportado

    def _diferencia(curva: list) -> Optional[float]:
        """Cuánto le sacó la cartera al benchmark, en puntos porcentuales."""
        variacion = _variacion(curva)
        if rendimiento is None or variacion is None:
            return None
        return round(rendimiento - variacion, 2)

    return {
        "moneda": moneda,
        "fechas": fechas,
        "cartera": cartera,
        "benchmarks": benchmarks,
        "valores": [punto["valor"] for punto in serie],
        "totales": {
            "desde": fechas[0],
            "hasta": fechas[-1],
            "twr_pct": rendimiento,
            "valor_actual": valor_final,
            # Lo que quedó puesto: aportes menos lo que salió por las ventas
            "aportado_neto": aportado,
            "ganancia": round(ganancia, 2),
            # Cuánto hizo cada benchmark y cuántos puntos le sacó la cartera
            "variaciones": {
                clave: _variacion(curva) for clave, curva in benchmarks.items()
            },
            "contra": {clave: _diferencia(curva) for clave, curva in benchmarks.items()},
            # Los que tienen tarjeta propia, a mano
            "mercado_pct": _variacion(benchmarks["mercado"]),
            "inflacion_pct": _variacion(benchmarks.get("inflacion", [])),
            "contra_mercado": _diferencia(benchmarks["mercado"]),
            "contra_inflacion": _diferencia(benchmarks.get("inflacion", [])),
        },
    }
