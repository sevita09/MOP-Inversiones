"""Cálculo y sincronización de las tasas del dólar.

CCL (Contado con Liquidación): se calcula a partir de GGAL en BYMA (ARS) y su
ADR en NYSE (USD). Cada ADR equivale a 10 acciones locales.

    CCL = (GGAL_ars * 10) / GGAL_adr_usd
"""
from __future__ import annotations

import sqlite3
from bisect import bisect_right
from datetime import datetime, timedelta, timezone

from app.config import TICKER_CCL_BASE, tickers_byma
from app.repositorios.tasas_dolar import CCL, OFICIAL, guardar_tasas, obtener_tasas
from app.repositorios.velas import guardar_velas, obtener_velas
from app.servicios.descarga import descargar_velas

# Cada ADR de GGAL en NYSE representa 10 acciones locales
ACCIONES_POR_ADR = 10

TICKER_CCL = "DOLARCCL"
TICKER_OFICIAL = "DOLAROF"


def _fecha_a_ts(fecha: str) -> int:
    return int(datetime.strptime(fecha, "%Y-%m-%d").replace(tzinfo=timezone.utc).timestamp())


def _por_fecha(velas: list[dict]) -> dict[str, dict]:
    """Indexa velas diarias por fecha AAAA-MM-DD (UTC)."""
    indexado = {}
    for vela in velas:
        fecha = datetime.fromtimestamp(vela["ts"], tz=timezone.utc).strftime("%Y-%m-%d")
        indexado[fecha] = vela
    return indexado


def calcular_ccl_diario(
    velas_ars: list[dict], velas_adr: list[dict]
) -> list[dict]:
    """Combina las series diarias de GGAL (ARS) y su ADR (USD) en tasas CCL.

    Solo emite tasa en las fechas donde hay vela real (no faltante) de ambos
    lados, con cierres positivos.
    """
    adr_por_fecha = _por_fecha(velas_adr)
    tasas = []
    for fecha, vela_ars in _por_fecha(velas_ars).items():
        vela_adr = adr_por_fecha.get(fecha)
        if vela_adr is None:
            continue
        if vela_ars.get("es_faltante") or vela_adr.get("es_faltante"):
            continue
        cierre_ars, cierre_adr = vela_ars["cierre"], vela_adr["cierre"]
        if cierre_ars <= 0 or cierre_adr <= 0:
            continue
        tasas.append(
            {
                "fecha": fecha,
                "tipo": CCL,
                "valor": round(cierre_ars * ACCIONES_POR_ADR / cierre_adr, 4),
            }
        )
    return sorted(tasas, key=lambda t: t["fecha"])


def sincronizar_ccl(conexion: sqlite3.Connection) -> int:
    """Recalcula la serie CCL desde las velas diarias guardadas. Devuelve cuántas."""
    velas_ars = obtener_velas(conexion, "GGAL", "D")
    velas_adr = obtener_velas(conexion, TICKER_CCL_BASE, "D")
    tasas = calcular_ccl_diario(velas_ars, velas_adr)
    return guardar_tasas(conexion, tasas) if tasas else 0


def _tasa_a_vela(ticker: str, fecha: str, valor: float) -> dict:
    """Una tasa diaria como vela sintética (OHLC = el valor de la tasa)."""
    return {
        "ticker": ticker,
        "temporalidad": "D",
        "ts": _fecha_a_ts(fecha),
        "apertura": valor,
        "maximo": valor,
        "minimo": valor,
        "cierre": valor,
        "volumen": 0.0,
        "es_faltante": 0,
    }


def _inicio_periodo(ts: int, temporalidad: str) -> int:
    """Inicio del período (lunes para S, día 1 para M) al que pertenece el ts."""
    fecha = datetime.fromtimestamp(ts, tz=timezone.utc)
    if temporalidad == "S":
        inicio = (fecha - timedelta(days=fecha.weekday())).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
    else:  # M
        inicio = fecha.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    return int(inicio.timestamp())


def resamplear(velas_diarias: list[dict], ticker: str, temporalidad: str) -> list[dict]:
    """Agrupa velas diarias en velas S o M (OHLC del período). Espera orden ascendente."""
    grupos: dict[int, list[dict]] = {}
    for vela in velas_diarias:
        grupos.setdefault(_inicio_periodo(vela["ts"], temporalidad), []).append(vela)
    return [
        {
            "ticker": ticker,
            "temporalidad": temporalidad,
            "ts": ts,
            "apertura": grupo[0]["apertura"],
            "maximo": max(v["maximo"] for v in grupo),
            "minimo": min(v["minimo"] for v in grupo),
            "cierre": grupo[-1]["cierre"],
            "volumen": sum(v["volumen"] for v in grupo),
            "es_faltante": 0,
        }
        for ts, grupo in sorted(grupos.items())
    ]


def _guardar_diaria_y_resampleos(
    conexion: sqlite3.Connection, ticker: str, velas_diarias: list[dict]
) -> int:
    """Guarda las velas diarias del dólar y sus resampleos S y M. La horaria no
    aplica: el dólar (CCL/oficial) es un valor de cierre diario, sin intradía real."""
    total = guardar_velas(conexion, velas_diarias)
    for temporalidad in ("S", "M"):
        resampleadas = resamplear(velas_diarias, ticker, temporalidad)
        if resampleadas:
            guardar_velas(conexion, resampleadas)
    return total


def generar_velas_ccl(conexion: sqlite3.Connection) -> int:
    """Crea velas sintéticas DOLARCCL (D, S, M) desde la serie de tasas CCL."""
    velas = [
        _tasa_a_vela(TICKER_CCL, tasa["fecha"], tasa["valor"])
        for tasa in obtener_tasas(conexion, CCL)
    ]
    return _guardar_diaria_y_resampleos(conexion, TICKER_CCL, velas) if velas else 0


def sincronizar_dolar_oficial(conexion: sqlite3.Connection) -> int:
    """Baja el dólar oficial de yfinance, lo guarda como velas DOLAROF (D, S, M) y como tasas."""
    velas = descargar_velas(TICKER_OFICIAL, "D")
    if not velas:
        return 0
    _guardar_diaria_y_resampleos(conexion, TICKER_OFICIAL, velas)
    tasas = [
        {
            "fecha": datetime.fromtimestamp(vela["ts"], tz=timezone.utc).strftime("%Y-%m-%d"),
            "tipo": OFICIAL,
            "valor": vela["cierre"],
        }
        for vela in velas
    ]
    guardar_tasas(conexion, tasas)
    return len(velas)


def se_convierte_a_usd(ticker: str, conexion: Optional[sqlite3.Connection] = None) -> bool:
    """Solo lo que cotiza en ARS se convierte: papeles BYMA de config y tickers
    agregados por el usuario con símbolo .BA. CEDEARs (subyacente USD), índices,
    cripto y dólares ya están en su moneda."""
    if ticker in tickers_byma():
        return True
    if conexion is not None:
        from app.repositorios.tickers_extra import simbolo_de

        simbolo = simbolo_de(conexion, ticker)
        return simbolo is not None and simbolo.endswith(".BA")
    return False


def serie_ccl(conexion: sqlite3.Connection) -> tuple[list[str], list[float]]:
    """Fechas y valores CCL ordenados, para resolver tasas con búsqueda binaria."""
    tasas = obtener_tasas(conexion, CCL)
    return [t["fecha"] for t in tasas], [t["valor"] for t in tasas]


def tasa_ccl_para_ts(
    fechas: list[str], valores: list[float], ts: int
) -> Optional[float]:
    """Tasa CCL vigente en la fecha del ts: la del día o la del hábil anterior."""
    fecha = datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y-%m-%d")
    posicion = bisect_right(fechas, fecha)
    return valores[posicion - 1] if posicion > 0 else None


def velas_para_vista(
    conexion: sqlite3.Connection,
    ticker: str,
    temporalidad: str,
    moneda: str,
    desde=None,
    hasta=None,
) -> list[dict]:
    """Velas del ticker en la moneda pedida.

    En USD: si la acción tiene ADR, devuelve la serie del ADR (precio real en el
    exterior, sin pasar por el CCL); si no, convierte la serie local por CCL.
    """
    from app.config import ADR, SUFIJO_ADR

    if moneda == "USD" and ticker in ADR:
        return obtener_velas(conexion, f"{ticker}{SUFIJO_ADR}", temporalidad, desde, hasta)
    velas = obtener_velas(conexion, ticker, temporalidad, desde, hasta)
    if moneda == "USD":
        velas = convertir_velas_a_usd(conexion, ticker, velas)
    return velas


def convertir_velas_a_usd(
    conexion: sqlite3.Connection, ticker: str, velas: list[dict]
) -> list[dict]:
    """Divide OHLC por la tasa CCL de cada fecha (la del día o la del hábil anterior).

    Carga las tasas una sola vez y resuelve cada vela con búsqueda binaria en
    memoria. Las velas anteriores a la primera tasa conocida se descartan.
    """
    if not se_convierte_a_usd(ticker, conexion) or not velas:
        return velas
    fechas, valores = serie_ccl(conexion)
    if not fechas:
        return []

    convertidas = []
    for vela in velas:
        tasa = tasa_ccl_para_ts(fechas, valores, vela["ts"])
        if tasa is None:
            continue  # sin tasa vigente para esa fecha
        convertidas.append(
            dict(
                vela,
                apertura=round(vela["apertura"] / tasa, 4),
                maximo=round(vela["maximo"] / tasa, 4),
                minimo=round(vela["minimo"] / tasa, 4),
                cierre=round(vela["cierre"] / tasa, 4),
            )
        )
    return convertidas
