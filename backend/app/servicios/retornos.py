"""Cálculo de los retornos logarítmicos que alimentan el análisis transversal.

**Por qué logarítmicos y no porcentuales:** se suman en el tiempo (el retorno de
un mes es la suma de sus días), son simétricos —subir y bajar lo mismo vuelve a
cero— y la correlación sobre ellos es la que corresponde. Además, pasar una
serie a dólares es restarle el retorno del dólar, no dividir.

    r_t = ln(cierre_t / cierre_(t−1))

**Las velas faltantes no generan retorno**: un placeholder o una vela
interpolada no es un precio que existió, y un retorno calculado contra ella
sería inventado. Si falta una rueda del medio, esa fecha simplemente no tiene
retorno — la serie sigue en la siguiente vela real, sin fabricar un salto de dos
días.

Se guardan en ARS y en USD porque son preguntas distintas: en pesos la
estacionalidad la distorsiona la inflación, y en las correlaciones el factor
dólar común las infla a todas. La conversión usa `velas_para_vista`, la misma
del gráfico (con ADR cuando el papel tiene certificado).
"""
from __future__ import annotations

import math
import sqlite3
from typing import Optional

from app.config import TEMPORALIDADES_BOTS
from app.repositorios import retornos as repo
from app.servicios.dolar import velas_para_vista
from app.servicios.tickers_extra import universo_completo

MONEDAS = ("ARS", "USD")

# D, S y M: la horaria no aporta a estacionalidad ni correlaciones
TEMPORALIDADES = TEMPORALIDADES_BOTS


def calcular(velas: list[dict], ticker: str, temporalidad: str, moneda: str) -> list[dict]:
    """Retornos log de una serie de velas, salteando las faltantes.

    Cada retorno se ata a la vela de llegada: el de una rueda es lo que se ganó
    o perdió *ese* día.
    """
    salida = []
    anterior: Optional[dict] = None
    for vela in velas:
        if vela.get("es_faltante") or vela["cierre"] <= 0:
            continue
        if anterior is not None:
            salida.append(
                {
                    "ticker": ticker,
                    "temporalidad": temporalidad,
                    "moneda": moneda,
                    "ts": vela["ts"],
                    "retorno": round(math.log(vela["cierre"] / anterior["cierre"]), 8),
                }
            )
        anterior = vela
    return salida


def recalcular_serie(
    conexion: sqlite3.Connection,
    ticker: str,
    temporalidad: str,
    moneda: str,
    completo: bool = False,
) -> int:
    """Recalcula los retornos de una serie. Devuelve cuántos guardó.

    Por defecto sigue desde el último retorno guardado (arrastrando una vela
    previa para poder encadenar); con `completo` rehace toda la historia.
    """
    desde = None
    ultimo = None if completo else repo.ultimo_ts(conexion, ticker, temporalidad, moneda)
    if ultimo is not None:
        # Un paso atrás: el primer retorno nuevo necesita su vela anterior
        desde = _vela_previa(conexion, ticker, temporalidad, ultimo)

    velas = velas_para_vista(conexion, ticker, temporalidad, moneda, desde=desde)
    nuevos = calcular(velas, ticker, temporalidad, moneda)
    if ultimo is not None:
        # La vela arrastrada vuelve a producir el último retorno ya guardado
        nuevos = [r for r in nuevos if r["ts"] > ultimo]
    return repo.guardar(conexion, nuevos)


def _vela_previa(
    conexion: sqlite3.Connection, ticker: str, temporalidad: str, ts: int
) -> Optional[int]:
    """El ts de la vela real anterior a `ts` (la que encadena el primer retorno)."""
    fila = conexion.execute(
        """SELECT ts FROM velas
           WHERE ticker = ? AND temporalidad = ? AND ts < ? AND es_faltante = 0
           ORDER BY ts DESC LIMIT 1""",
        (ticker, temporalidad, ts),
    ).fetchone()
    return fila["ts"] if fila else None


def recalcular_todo(conexion: sqlite3.Connection, completo: bool = False) -> dict:
    """Actualiza los retornos de todo el universo tras un sync.

    Es incremental por diseño: el sync corre cada 15 minutos y rehacer diez años
    de historia cada vez sería tirar trabajo a la basura.
    """
    guardados = 0
    errores = []
    for ticker in sorted(universo_completo(conexion)):
        for temporalidad in TEMPORALIDADES:
            for moneda in MONEDAS:
                try:
                    guardados += recalcular_serie(
                        conexion, ticker, temporalidad, moneda, completo
                    )
                except Exception as error:  # una serie rota no frena al resto
                    errores.append(f"{ticker}/{temporalidad}/{moneda}: {error}")
    return {"guardados": guardados, "errores": errores}
