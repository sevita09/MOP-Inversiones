"""Correlación entre papeles, sobre retornos y nunca sobre precios.

Dos series de **precios** con tendencia dan correlación altísima aunque no
tengan nada que ver: las dos suben, y eso alcanza. La correlación se calcula
sobre los **retornos logarítmicos** precalculados (v8.1), que es lo que mide si
se mueven juntos día a día.

**El toggle de moneda importa acá más que en ningún lado.** En pesos, todo papel
argentino carga el mismo factor —la devaluación— y eso infla todas las
correlaciones hacia arriba: parece que la cartera está diversificada en papeles
que en realidad se mueven juntos. En dólares queda la correlación de los
negocios, que es la que sirve para decidir si dos posiciones son una sola.

Solo se usan las fechas donde **los dos** papeles operaron: si uno no tuvo rueda
ese día, ese día no dice nada sobre cómo se mueven juntos.
"""
from __future__ import annotations

import math
import sqlite3
from typing import Optional

from app.repositorios import retornos as repo

# Con menos que esto el coeficiente es ruido: dos meses de datos pueden dar
# correlación 0,9 por casualidad
MINIMO_DE_PARES = 30

# Una serie constante no tiene varianza, pero en punto flotante la suma de sus
# desvíos da algo como 1e-35 en vez de cero — y dividir por eso devuelve un
# coeficiente inventado. La varianza de retornos reales está muchos órdenes de
# magnitud por encima de este piso.
VARIANZA_MINIMA = 1e-18


def correlacion(serie_a: list[float], serie_b: list[float]) -> Optional[float]:
    """Coeficiente de Pearson entre dos series ya alineadas.

    `None` si alguna serie no varía (una constante no correlaciona con nada:
    la fórmula dividiría por cero).
    """
    n = len(serie_a)
    if n < 2 or n != len(serie_b):
        return None

    media_a = sum(serie_a) / n
    media_b = sum(serie_b) / n
    covarianza = sum((a - media_a) * (b - media_b) for a, b in zip(serie_a, serie_b))
    varianza_a = sum((a - media_a) ** 2 for a in serie_a)
    varianza_b = sum((b - media_b) ** 2 for b in serie_b)
    if varianza_a < VARIANZA_MINIMA or varianza_b < VARIANZA_MINIMA:
        return None
    return covarianza / math.sqrt(varianza_a * varianza_b)


def _series_comunes(
    matriz: dict, a: str, b: str
) -> tuple[list[float], list[float]]:
    """Los retornos de los dos papeles en las fechas donde ambos operaron."""
    serie_a, serie_b = [], []
    for fecha in sorted(matriz):
        fila = matriz[fecha]
        if a in fila and b in fila:
            serie_a.append(fila[a])
            serie_b.append(fila[b])
    return serie_a, serie_b


def matriz_correlacion(
    conexion: sqlite3.Connection,
    tickers: list[str],
    temporalidad: str = "D",
    moneda: str = "USD",
    desde: Optional[int] = None,
    minimo: int = MINIMO_DE_PARES,
) -> dict:
    """Matriz de correlación entre todos los pares de la lista.

    La diagonal es 1 por definición y la matriz es simétrica: se calcula media y
    se refleja, que es la mitad del trabajo.
    """
    tickers = list(dict.fromkeys(t.upper() for t in tickers))
    datos = repo.alineados(conexion, tickers, temporalidad, moneda, desde)

    tamano = len(tickers)
    matriz: list[list[Optional[float]]] = [[None] * tamano for _ in range(tamano)]
    pares: list[list[int]] = [[0] * tamano for _ in range(tamano)]

    for i in range(tamano):
        matriz[i][i] = 1.0
        for j in range(i + 1, tamano):
            serie_a, serie_b = _series_comunes(datos, tickers[i], tickers[j])
            pares[i][j] = pares[j][i] = len(serie_a)
            valor = correlacion(serie_a, serie_b) if len(serie_a) >= minimo else None
            valor = None if valor is None else round(valor, 4)
            matriz[i][j] = matriz[j][i] = valor
        pares[i][i] = len(
            [1 for fila in datos.values() if tickers[i] in fila]
        )

    return {
        "tickers": tickers,
        "temporalidad": temporalidad,
        "moneda": moneda,
        "matriz": matriz,
        "pares": pares,
        "minimo": minimo,
    }


def _moviles(serie_a: list, serie_b: list, ventana: int) -> list:
    """Pearson en ventana móvil, con sumas corridas.

    O(n) en vez de O(n×ventana): recalcular cada ventana desde cero era un
    segundo entero con diez años y ventana de 630.
    """
    n = len(serie_a)
    salida: list = [None] * n
    if ventana < 2 or n < ventana:
        return salida

    suma_a = suma_b = suma_aa = suma_bb = suma_ab = 0.0
    for i in range(n):
        a, b = serie_a[i], serie_b[i]
        suma_a += a
        suma_b += b
        suma_aa += a * a
        suma_bb += b * b
        suma_ab += a * b
        if i >= ventana:
            viejo_a, viejo_b = serie_a[i - ventana], serie_b[i - ventana]
            suma_a -= viejo_a
            suma_b -= viejo_b
            suma_aa -= viejo_a * viejo_a
            suma_bb -= viejo_b * viejo_b
            suma_ab -= viejo_a * viejo_b
        if i >= ventana - 1:
            covarianza = suma_ab - suma_a * suma_b / ventana
            varianza_a = suma_aa - suma_a * suma_a / ventana
            varianza_b = suma_bb - suma_b * suma_b / ventana
            if varianza_a > VARIANZA_MINIMA and varianza_b > VARIANZA_MINIMA:
                salida[i] = covarianza / math.sqrt(varianza_a * varianza_b)
    return salida


def rolling(
    conexion: sqlite3.Connection,
    a: str,
    b: str,
    temporalidad: str = "D",
    moneda: str = "USD",
    ventana: int = 60,
    desde: Optional[int] = None,
) -> dict:
    """Correlación móvil entre dos papeles: cómo cambió en el tiempo.

    Un coeficiente único sobre diez años esconde lo que importa: dos papeles
    pueden haber estado descorrelacionados años y pegarse en una crisis, que es
    justo cuando la diversificación tendría que servir.
    """
    a, b = a.upper(), b.upper()
    # Se traen TODAS las ruedas, no solo las del período: la ventana necesita
    # historia previa para arrancar. Sin ese calentamiento el gráfico empezaría
    # una ventana entera después del inicio del período —con 2 años y ventana de
    # medio año, el primer punto caía seis meses tarde.
    datos = repo.alineados(conexion, [a, b], temporalidad, moneda)
    fechas = [f for f in sorted(datos) if a in datos[f] and b in datos[f]]
    serie_a = [datos[f][a] for f in fechas]
    serie_b = [datos[f][b] for f in fechas]

    moviles = _moviles(serie_a, serie_b, ventana)
    visible = [i for i, f in enumerate(fechas) if desde is None or f >= desde]
    puntos = [
        {"ts": fechas[i], "correlacion": round(moviles[i], 4)}
        for i in visible
        if moviles[i] is not None
    ]

    # El coeficiente del recuadro es el del período que se está mirando
    completa = correlacion([serie_a[i] for i in visible], [serie_b[i] for i in visible])
    fechas = [fechas[i] for i in visible]
    return {
        "a": a,
        "b": b,
        "temporalidad": temporalidad,
        "moneda": moneda,
        "ventana": ventana,
        "puntos": puntos,
        "correlacion_total": None if completa is None else round(completa, 4),
        "correlacion_ventana": puntos[-1]["correlacion"] if puntos else None,
        "pares": len(fechas),
        # La nube son todas las ruedas del período consultado: la línea resume
        # cómo fue cambiando y la nube muestra la materia prima de ese tramo
        "dispersion": [
            {"ts": f, "a": round(datos[f][a], 6), "b": round(datos[f][b], 6)}
            for f in fechas
        ],
    }
