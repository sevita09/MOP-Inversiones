"""Estacionalidad: ¿hay meses o días que históricamente rinden distinto?

El cuadro clásico años×meses, armado sobre los **retornos logarítmicos**
precalculados (v8.1). Cada celda del cuadro mensual es el retorno de ese mes;
en la vista por día de la semana es el promedio de los retornos de ese día en
ese año.

**El default es en dólares.** En pesos la inflación mete un piso positivo en
todos los meses y el cuadro deja de decir nada: los doce quedan verdes.

Las estadísticas se calculan sobre los logaritmos y recién al final se pasan a
porcentaje. Promediar porcentajes de períodos encadenados da un número que no
corresponde a ningún recorrido real; el promedio de los logs sí (es la media
geométrica). La mediana no tiene ese problema —el orden se conserva— pero se
calcula igual para que las dos salgan del mismo lugar.
"""
from __future__ import annotations

import math
import sqlite3
import statistics
from datetime import datetime, timezone
from typing import Optional

from app.repositorios import retornos as repo

MESES = [
    "Ene", "Feb", "Mar", "Abr", "May", "Jun",
    "Jul", "Ago", "Sep", "Oct", "Nov", "Dic",
]
# El mercado no opera fin de semana: sábado y domingo no entran
DIAS = ["Lun", "Mar", "Mié", "Jue", "Vie"]


def _a_porcentaje(logaritmico: Optional[float]) -> Optional[float]:
    """De retorno logarítmico a la variación que se lee: 0,0953 → +10,0%."""
    if logaritmico is None:
        return None
    return round((math.exp(logaritmico) - 1) * 100, 2)


def _estadisticas(valores: list[float]) -> dict:
    """Promedio, mediana y proporción de períodos positivos de una columna."""
    if not valores:
        return {"promedio_pct": None, "mediana_pct": None, "positivos_pct": None, "casos": 0}
    positivos = sum(1 for v in valores if v > 0)
    return {
        "promedio_pct": _a_porcentaje(sum(valores) / len(valores)),
        "mediana_pct": _a_porcentaje(statistics.median(valores)),
        "positivos_pct": round(positivos / len(valores) * 100, 1),
        "casos": len(valores),
    }


def _armar(
    ticker: str,
    moneda: str,
    columnas: list[str],
    celdas: dict,
    totales: dict,
    detalle: str,
    poblacion: Optional[dict] = None,
) -> dict:
    """Envuelve el cuadro en la forma que espera el mapa de calor.

    `celdas` es `{(anio, indice_columna): retorno log}` y `totales` el acumulado
    de cada año. Los años van del más viejo al más nuevo: el cuadro se lee hacia
    abajo, como una línea de tiempo, y el año en curso queda contra el resumen.

    `poblacion` son los valores sobre los que se calcula la fila de resumen,
    cuando no coinciden con las celdas: en el cuadro mensual cada celda **es**
    una observación, pero en el de días la celda ya es un promedio de unas
    cincuenta ruedas, y resumir sobre promedios anuales tiraría la muestra real
    a la basura.
    """
    anios = sorted({anio for anio, _ in celdas})
    matriz = [
        [_a_porcentaje(celdas.get((anio, indice))) for indice in range(len(columnas))]
        for anio in anios
    ]
    resumen = [
        _estadisticas(
            poblacion[indice]
            if poblacion is not None
            else [celdas[(anio, indice)] for anio in anios if (anio, indice) in celdas]
        )
        for indice in range(len(columnas))
    ]
    return {
        "ticker": ticker,
        "moneda": moneda,
        "detalle": detalle,
        "columnas": columnas,
        "anios": anios,
        "matriz": matriz,
        "totales_anio": [_a_porcentaje(totales.get(anio)) for anio in anios],
        "resumen": resumen,
    }


def por_mes(conexion: sqlite3.Connection, ticker: str, moneda: str = "USD") -> dict:
    """Cuadro años×meses: cada celda es el retorno de ese mes."""
    celdas: dict = {}
    totales: dict = {}
    for retorno in repo.obtener(conexion, ticker, "M", moneda):
        fecha = datetime.fromtimestamp(retorno["ts"], tz=timezone.utc)
        celdas[(fecha.year, fecha.month - 1)] = retorno["retorno"]
        totales[fecha.year] = totales.get(fecha.year, 0.0) + retorno["retorno"]
    return _armar(ticker, moneda, MESES, celdas, totales, "retorno del mes")


def por_dia_semana(conexion: sqlite3.Connection, ticker: str, moneda: str = "USD") -> dict:
    """Cuadro años×días: cada celda es el retorno promedio de ese día ese año.

    Acá la celda no puede ser la suma como en el cuadro mensual: un año tiene
    unas cincuenta ruedas de cada día, y sumarlas mediría cuántos lunes hubo más
    que cómo son los lunes.
    """
    acumulado: dict = {}
    totales: dict = {}
    for retorno in repo.obtener(conexion, ticker, "D", moneda):
        fecha = datetime.fromtimestamp(retorno["ts"], tz=timezone.utc)
        if fecha.weekday() >= len(DIAS):
            continue
        acumulado.setdefault((fecha.year, fecha.weekday()), []).append(retorno["retorno"])
        totales[fecha.year] = totales.get(fecha.year, 0.0) + retorno["retorno"]

    celdas = {clave: sum(valores) / len(valores) for clave, valores in acumulado.items()}
    # La fila de resumen mira todas las ruedas, no el promedio de cada año
    poblacion: dict = {indice: [] for indice in range(len(DIAS))}
    for (_, dia), valores in acumulado.items():
        poblacion[dia] += valores

    return _armar(
        ticker, moneda, DIAS, celdas, totales, "retorno promedio del día", poblacion
    )
