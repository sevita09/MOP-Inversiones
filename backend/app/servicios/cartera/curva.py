"""Curva diaria de valor de la cartera y flujos de capital.

Para cada rueda: cuántos papeles se tenían de cada especie (reconstruido desde
las operaciones y los splits) por el cierre de ese día. Aparte, el **flujo** de
esa rueda: lo que se puso al comprar (precio + gastos) y lo que se sacó al
vender (precio − gastos).

Separar valor de flujo es lo que después permite calcular el TWR: una cartera
que sube porque le metiste plata no rindió nada, y el retorno simple no sabe
distinguirlo.
"""
from __future__ import annotations

import sqlite3
from bisect import bisect_right
from datetime import datetime, timezone
from typing import Optional

from app.repositorios import splits as repo_splits
from app.repositorios import transacciones as repo
from app.servicios.cartera import TIPO_DOLAR
from app.servicios.cartera.posiciones import eventos_ordenados
from app.servicios.dolar import se_convierte_a_usd


def _fecha_de(ts: int) -> str:
    return datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y-%m-%d")


def _cierres_diarios(conexion: sqlite3.Connection, ticker: str) -> tuple[list, list]:
    """Fechas y cierres diarios reales del papel, para buscar por fecha."""
    filas = conexion.execute(
        """SELECT ts, cierre FROM velas
           WHERE ticker = ? AND temporalidad = 'D' AND es_faltante = 0
           ORDER BY ts""",
        (ticker,),
    ).fetchall()
    return [_fecha_de(f["ts"]) for f in filas], [f["cierre"] for f in filas]


def _valor_en(fechas: list, valores: list, fecha: str) -> Optional[float]:
    """El último valor conocido hasta esa fecha (la rueda del día o la anterior)."""
    posicion = bisect_right(fechas, fecha)
    return valores[posicion - 1] if posicion > 0 else None


def serie_de_tasas(conexion: sqlite3.Connection, tipo: str = TIPO_DOLAR) -> tuple[list, list]:
    """Fechas y valores de un tipo de dólar, para buscar la vigente en cada rueda."""
    filas = conexion.execute(
        "SELECT fecha, valor FROM tasas_dolar WHERE tipo = ? ORDER BY fecha", (tipo,)
    ).fetchall()
    return [f["fecha"] for f in filas], [f["valor"] for f in filas]


def tasas_alineadas(conexion: sqlite3.Connection, tipo: str, fechas: list) -> list:
    """El dólar de cada rueda pedida (la de ese día o la de la anterior)."""
    disponibles = serie_de_tasas(conexion, tipo)
    return [_valor_en(*disponibles, fecha) for fecha in fechas]


def _cantidades_y_flujos(conexion: sqlite3.Connection) -> tuple[dict, dict]:
    """Recorre todas las operaciones y devuelve, por fecha:

    - `cantidades[fecha][ticker]`: los papeles que quedan de esa especie al
      cerrar esa rueda (ya ajustados por splits);
    - `flujos[fecha]`: la plata neta que entró (compras) o salió (ventas).
    """
    cantidades: dict = {}
    flujos: dict = {}
    tenencia: dict = {}

    eventos = []
    for ticker in repo.tickers_operados(conexion):
        eventos += eventos_ordenados(
            repo.listar_cronologicas(conexion, ticker),
            repo_splits.listar_cronologicos(conexion, ticker),
        )
    eventos.sort(key=lambda e: e["_orden"])

    for evento in eventos:
        ticker = evento["ticker"]
        if evento["tipo"] == "split":
            tenencia[ticker] = tenencia.get(ticker, 0) * evento["ratio"]
        elif evento["tipo"] == "compra":
            tenencia[ticker] = tenencia.get(ticker, 0) + evento["cantidad"]
            bruto = evento["cantidad"] * evento["precio"]
            flujos[evento["fecha"]] = flujos.get(evento["fecha"], 0) + bruto + evento["comision"]
        else:
            tenencia[ticker] = tenencia.get(ticker, 0) - evento["cantidad"]
            bruto = evento["cantidad"] * evento["precio"]
            flujos[evento["fecha"]] = flujos.get(evento["fecha"], 0) - bruto + evento["comision"]
        cantidades[evento["fecha"]] = dict(tenencia)

    return cantidades, flujos


def _calendario(conexion: sqlite3.Connection, tickers: list, desde: str) -> list:
    """Ruedas del mercado desde la primera operación hasta la última con datos."""
    if not tickers:
        return []
    marcadores = ",".join("?" * len(tickers))
    filas = conexion.execute(
        f"""SELECT DISTINCT ts FROM velas
            WHERE ticker IN ({marcadores}) AND temporalidad = 'D' AND es_faltante = 0
            ORDER BY ts""",
        tickers,
    ).fetchall()
    return [f for f in (_fecha_de(fila["ts"]) for fila in filas) if f >= desde]


def serie_valor(
    conexion: sqlite3.Connection, moneda: str = "ARS", desde: Optional[str] = None
) -> list[dict]:
    """Valor de la cartera rueda por rueda, con el flujo de capital de cada día.

    En USD todo se convierte con el MEP de **esa** rueda: es lo que valía la
    cartera en dólares ese día, no el valor de hoy pasado por el dólar de hoy.
    """
    operaciones = repo.listar_cronologicas(conexion)
    if not operaciones:
        return []

    cantidades, flujos = _cantidades_y_flujos(conexion)
    fechas_con_movimiento = sorted(cantidades)
    tickers = repo.tickers_operados(conexion)
    inicio = max(desde, fechas_con_movimiento[0]) if desde else fechas_con_movimiento[0]

    precios = {t: _cierres_diarios(conexion, t) for t in tickers}
    fechas_dolar, valores_dolar = serie_de_tasas(conexion)

    # Un flujo puede caer un día sin rueda (una operación cargada un sábado):
    # se imputa a la primera rueda posterior, para no perderlo. Con `desde`, los
    # anteriores al rango quedan afuera: son de un período que no se está midiendo.
    fechas_con_flujo = sorted(f for f in flujos if not desde or f >= desde)

    serie = []
    tenencia: dict = {}
    indice = 0
    indice_flujo = 0
    for fecha in _calendario(conexion, tickers, inicio):
        # Arrastra todas las operaciones hasta esta rueda (incluidas las
        # anteriores al inicio del rango: la posición viene de antes)
        while indice < len(fechas_con_movimiento) and fechas_con_movimiento[indice] <= fecha:
            tenencia = cantidades[fechas_con_movimiento[indice]]
            indice += 1

        flujo = 0.0
        while indice_flujo < len(fechas_con_flujo) and fechas_con_flujo[indice_flujo] <= fecha:
            flujo += flujos[fechas_con_flujo[indice_flujo]]
            indice_flujo += 1

        valor = 0.0
        for ticker, cantidad in tenencia.items():
            if cantidad <= 1e-9:
                continue
            cierre = _valor_en(*precios[ticker], fecha)
            if cierre is not None:
                valor += cantidad * cierre

        if moneda == "USD":
            tasa = _valor_en(fechas_dolar, valores_dolar, fecha)
            if not tasa:
                continue  # sin MEP de esa rueda no hay punto en dólares
            valor, flujo = valor / tasa, flujo / tasa

        serie.append({"fecha": fecha, "valor": round(valor, 2), "flujo": round(flujo, 2)})
    return serie


def serie_de_precios(
    conexion: sqlite3.Connection, ticker: str, moneda: str, fechas: list
) -> list:
    """Cierres del papel alineados a las fechas pedidas (para los benchmarks).

    Convierte en las dos direcciones, siempre con el MEP de esa rueda:

    - lo que cotiza en pesos (el MERVAL) se **divide** para verlo en dólares;
    - lo que cotiza en dólares (SPY, QQQ, BTC) se **multiplica** para verlo en
      pesos, que es lo que hubiera valido tenerlo acá.
    """
    disponibles = _cierres_diarios(conexion, ticker)
    en_pesos = se_convierte_a_usd(ticker, conexion)
    a_dolares = moneda == "USD" and en_pesos
    a_pesos = moneda == "ARS" and not en_pesos
    fechas_dolar, valores_dolar = (
        serie_de_tasas(conexion) if a_dolares or a_pesos else ([], [])
    )

    serie = []
    for fecha in fechas:
        cierre = _valor_en(*disponibles, fecha)
        if cierre is not None and (a_dolares or a_pesos):
            tasa = _valor_en(fechas_dolar, valores_dolar, fecha)
            if not tasa:
                cierre = None
            else:
                cierre = cierre / tasa if a_dolares else cierre * tasa
        serie.append(cierre)
    return serie
