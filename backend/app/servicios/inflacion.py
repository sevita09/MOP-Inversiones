"""Inflación mensual como benchmark de la cartera en pesos.

Un rendimiento en pesos no dice nada solo: 60% anual es una pérdida si los
precios subieron 80%. La fuente es el **IPC nacional del INDEC** publicado por
`api.argentinadatos.com`, que entrega la variación porcentual de cada mes.

La serie mensual se convierte en un **índice acumulado** encadenando los meses
(`índice *= 1 + variación/100`). Dentro del mes el índice no se mueve: el dato
es mensual y se publica a mediados del mes siguiente, así que inventar un
recorrido diario sería dibujar precisión que no existe.
"""
from __future__ import annotations

import json
import math
import sqlite3
import urllib.request
from bisect import bisect_right
from datetime import datetime, timedelta, timezone
from typing import Optional

from app.repositorios import configuracion as repo_config

TICKER = "INFLACION"

URL_INFLACION = "https://api.argentinadatos.com/v1/finanzas/indices/inflacion"
TIEMPO_LIMITE = 20

# La API rechaza el User-Agent que manda urllib por defecto (403)
CABECERAS = {"User-Agent": "MOP-Inversiones/1.0"}

# El INDEC publica el IPC del mes anterior alrededor del 13. Se consulta una vez
# por hora entre el 11 y el 15: antes no hay nada nuevo y después ya se bajó.
DIA_DESDE = 11
DIA_HASTA = 15
CLAVE_ULTIMO_INTENTO = "inflacion.ultimo_intento"


def descargar_inflacion(url: str = URL_INFLACION) -> list[dict]:
    """Baja la serie mensual. Devuelve [] si la fuente no responde.

    Que falle no puede romper el sync: sin dato nuevo se sigue con el guardado.
    """
    try:
        pedido = urllib.request.Request(url, headers=CABECERAS)
        with urllib.request.urlopen(pedido, timeout=TIEMPO_LIMITE) as respuesta:
            datos = json.loads(respuesta.read())
    except Exception:
        return []
    return [
        {"fecha": d["fecha"], "valor": float(d["valor"])}
        for d in datos
        if d.get("fecha") and d.get("valor") is not None
    ]


def guardar_inflacion(conexion: sqlite3.Connection, meses: list[dict]) -> int:
    if not meses:
        return 0
    conexion.executemany(
        "INSERT OR REPLACE INTO inflacion (fecha, valor) VALUES (?, ?)",
        [(m["fecha"], m["valor"]) for m in meses],
    )
    conexion.commit()
    return len(meses)


def hay_datos(conexion: sqlite3.Connection) -> bool:
    return conexion.execute("SELECT 1 FROM inflacion LIMIT 1").fetchone() is not None


def corresponde_consultar(conexion: sqlite3.Connection, ahora: Optional[datetime] = None) -> bool:
    """True si toca pegarle a la API.

    El dato es mensual: consultarlo en cada sync sería castigar a la fuente para
    nada. Se consulta entre el 11 y el 15, una vez por hora — salvo que la base
    esté vacía, donde hace falta la carga inicial.
    """
    if not hay_datos(conexion):
        return True
    ahora = ahora or datetime.now()
    if not DIA_DESDE <= ahora.day <= DIA_HASTA:
        return False

    ultimo = repo_config.leer(conexion, CLAVE_ULTIMO_INTENTO)
    if not ultimo:
        return True
    try:
        return datetime.fromisoformat(ultimo) <= ahora - timedelta(hours=1)
    except ValueError:
        return True


def sincronizar_inflacion(
    conexion: sqlite3.Connection, ahora: Optional[datetime] = None
) -> int:
    """Refresca la serie mensual si toca consultarla. Devuelve cuántos meses guardó."""
    if not corresponde_consultar(conexion, ahora):
        return 0
    repo_config.guardar(conexion, CLAVE_ULTIMO_INTENTO, (ahora or datetime.now()).isoformat())
    return guardar_inflacion(conexion, descargar_inflacion())


def indice_acumulado(conexion: sqlite3.Connection) -> tuple[list, list]:
    """Fechas de corte y el índice de precios acumulado en cada una (base 1).

    El índice de un mes vale desde el cierre de ese mes en adelante: es cuando
    ya ocurrió esa inflación.
    """
    filas = conexion.execute("SELECT fecha, valor FROM inflacion ORDER BY fecha").fetchall()
    fechas, indices = [], []
    acumulado = 1.0
    for fila in filas:
        acumulado *= 1 + fila["valor"] / 100
        fechas.append(fila["fecha"])
        indices.append(acumulado)
    return fechas, indices


def indice_alineado(conexion: sqlite3.Connection, fechas: list) -> list:
    """El índice de precios vigente en cada rueda pedida (escalón mensual)."""
    cortes, indices = indice_acumulado(conexion)
    if not cortes:
        return [None] * len(fechas)

    alineado: list[Optional[float]] = []
    for fecha in fechas:
        posicion = bisect_right(cortes, fecha)
        alineado.append(indices[posicion - 1] if posicion > 0 else None)
    return alineado


def generar_retornos(conexion: sqlite3.Connection) -> int:
    """Publica la inflación como una serie de retornos más, para correlacionar.

    Va en la tabla `retornos` bajo el ticker `INFLACION`, temporalidad mensual —
    la única que tiene sentido: el dato es mensual y cruzarlo contra ruedas
    diarias no diría nada.

    En **ARS** es la variación del mes. En **USD** es esa variación menos lo que
    se movió el dólar: cuánto subieron los precios *medidos en dólares*, que es
    la pregunta real de si algo se encareció o solo se devaluó el peso. Sale de
    restar los logaritmos, que es la propiedad por la que se usan.
    """
    from app.repositorios import retornos as repo_retornos
    from app.servicios.dolar import TICKER_MEP

    dolar = {
        r["ts"]: r["retorno"]
        for r in repo_retornos.obtener(conexion, TICKER_MEP, "M", "ARS")
    }

    salida = []
    for fila in conexion.execute("SELECT fecha, valor FROM inflacion ORDER BY fecha"):
        mes = datetime.strptime(fila["fecha"], "%Y-%m-%d").replace(
            day=1, tzinfo=timezone.utc
        )
        ts = int(mes.timestamp())
        en_pesos = math.log(1 + fila["valor"] / 100)
        salida.append(
            {"ticker": TICKER, "temporalidad": "M", "moneda": "ARS", "ts": ts,
             "retorno": round(en_pesos, 8)}
        )
        if ts in dolar:
            salida.append(
                {"ticker": TICKER, "temporalidad": "M", "moneda": "USD", "ts": ts,
                 "retorno": round(en_pesos - dolar[ts], 8)}
            )
    return repo_retornos.guardar(conexion, salida)
