from __future__ import annotations

import sqlite3
import threading
from datetime import datetime, timezone
from typing import Optional

from app.config import TEMPORALIDADES, todos_los_tickers
from app.repositorios.registro_sync import obtener_ultima_sync, registrar_sync
from app.repositorios.velas import (
    guardar_velas,
    obtener_ultima_vela,
    obtener_ultimo_ts,
    obtener_velas,
)
from app.db import obtener_conexion
from app.servicios.descarga import descargar_velas
from app.servicios.programador import INTERVALO_RUEDA, en_rueda

# Un solo sync a la vez: SQLite no banca escrituras concurrentes y
# el arranque y el endpoint manual pueden dispararlo al mismo tiempo
_lock_sync = threading.Lock()
_ultimo_resumen: Optional[dict] = None

# Cuánto puede envejecer el dato antes de volver a sincronizar (segundos)
VIGENCIA_POR_TEMPORALIDAD = {
    "H": 3600,
    "D": 86400,
    "S": 7 * 86400,
    "M": 30 * 86400,
}


def vigencia_actual(temporalidad: str, ahora: Optional[datetime] = None) -> float:
    """En rueda, la vela horaria y la diaria en curso envejecen a los 15 minutos
    (los precios se mueven); fuera de rueda rigen las vigencias normales."""
    if temporalidad in ("H", "D") and en_rueda(ahora):
        return INTERVALO_RUEDA
    return VIGENCIA_POR_TEMPORALIDAD[temporalidad]


def esta_vencido(
    ultima_sync: Optional[str],
    temporalidad: str,
    ahora: Optional[datetime] = None,
) -> bool:
    """Un dato está vencido si nunca se sincronizó o si pasó su vigencia."""
    if ultima_sync is None:
        return True
    ahora = ahora or datetime.now(timezone.utc)
    transcurrido = (ahora - datetime.fromisoformat(ultima_sync)).total_seconds()
    return transcurrido >= vigencia_actual(temporalidad, ahora)


def sincronizar_ticker(
    conexion: sqlite3.Connection,
    ticker: str,
    temporalidad: str,
    ahora: Optional[datetime] = None,
    simbolo: Optional[str] = None,
) -> int:
    """Sincroniza un ticker/temporalidad si está vencido. Devuelve velas guardadas.

    La primera vez baja toda la historia configurada; después solo el delta
    desde la última vela guardada (inclusive, para refrescar la vela en curso).
    `simbolo` fuerza el símbolo de Yahoo (tickers agregados por el usuario).
    """
    ahora = ahora or datetime.now(timezone.utc)
    if not esta_vencido(obtener_ultima_sync(conexion, ticker, temporalidad), temporalidad, ahora):
        return 0

    desde = obtener_ultimo_ts(conexion, ticker, temporalidad)
    velas = descargar_velas(ticker, temporalidad, desde=desde, simbolo=simbolo)
    guardadas = guardar_velas(conexion, velas) if velas else 0
    registrar_sync(conexion, ticker, temporalidad, ahora.isoformat())
    return guardadas


def _fin_de_periodo(ts: int, temporalidad: str) -> int:
    """Primer instante del período siguiente al de la vela que arranca en ts."""
    if temporalidad == "S":
        return ts + 7 * 86400
    inicio = datetime.fromtimestamp(ts, tz=timezone.utc)
    if inicio.month == 12:
        fin = inicio.replace(year=inicio.year + 1, month=1, day=1)
    else:
        fin = inicio.replace(month=inicio.month + 1, day=1)
    return int(fin.replace(hour=0, minute=0, second=0, microsecond=0).timestamp())


def refrescar_velas_en_curso(conexion: sqlite3.Connection, ticker: str) -> int:
    """Completa las velas S y M en curso con las diarias cuando D está más al día.

    S y M tienen vigencias largas; entre sync y sync, su última vela queda con el
    cierre viejo. Si la diaria se sincronizó después, el cierre pasa a ser el último
    cierre diario del período (y los extremos y el volumen se recalculan con las
    diarias). El próximo sync real de S/M pisa la vela con el dato de yfinance.
    """
    sync_diaria = obtener_ultima_sync(conexion, ticker, "D")
    if sync_diaria is None:
        return 0

    refrescadas = 0
    for temporalidad in ("S", "M"):
        sync_propia = obtener_ultima_sync(conexion, ticker, temporalidad)
        if sync_propia is None or sync_propia >= sync_diaria:
            continue
        vela = obtener_ultima_vela(conexion, ticker, temporalidad)
        if vela is None:
            continue
        diarias = obtener_velas(
            conexion,
            ticker,
            "D",
            desde=vela["ts"],
            hasta=_fin_de_periodo(vela["ts"], temporalidad) - 1,
        )
        if not diarias:
            continue
        actualizada = dict(
            vela,
            cierre=diarias[-1]["cierre"],
            maximo=max([vela["maximo"]] + [d["maximo"] for d in diarias]),
            minimo=min([vela["minimo"]] + [d["minimo"] for d in diarias]),
            volumen=sum(d["volumen"] for d in diarias),
        )
        if actualizada != vela:
            guardar_velas(conexion, [actualizada])
            refrescadas += 1
    return refrescadas


def sincronizar_todo(
    conexion: sqlite3.Connection, ahora: Optional[datetime] = None
) -> dict:
    """Recorre todos los tickers y temporalidades. Devuelve el resumen del sync."""
    resumen = {
        "velas_guardadas": 0,
        "pares_sincronizados": 0,
        "velas_refrescadas": 0,
        "errores": [],
    }
    # Universo fijo de config + series ADR + tickers agregados por el usuario
    from app.config import ADR, SUFIJO_ADR
    from app.repositorios.tickers_extra import listar as listar_extras

    pares = [(t, None) for t in todos_los_tickers()]
    pares += [(f"{byma}{SUFIJO_ADR}", None) for byma in ADR]  # simbolo_yahoo lo resuelve
    pares += [(e["ticker"], e["simbolo_yf"]) for e in listar_extras(conexion)]
    for ticker, simbolo in pares:
        for temporalidad in TEMPORALIDADES:
            try:
                guardadas = sincronizar_ticker(conexion, ticker, temporalidad, ahora, simbolo)
            except Exception as error:
                resumen["errores"].append(f"{ticker}/{temporalidad}: {error}")
                continue
            if guardadas:
                resumen["velas_guardadas"] += guardadas
                resumen["pares_sincronizados"] += 1
        resumen["velas_refrescadas"] += refrescar_velas_en_curso(conexion, ticker)
    return resumen


def hay_sync_en_curso() -> bool:
    return _lock_sync.locked()


def ultimo_resumen() -> Optional[dict]:
    return _ultimo_resumen


def sincronizar_en_background() -> bool:
    """Lanza sincronizar_todo en un thread aparte.

    Devuelve False sin hacer nada si ya hay un sync corriendo.
    """
    if not _lock_sync.acquire(blocking=False):
        return False

    def _correr():
        global _ultimo_resumen
        # Import acá para no acoplar el módulo al reparador ni al dólar en usos directos
        from app.servicios.dolar import (
            generar_velas_ccl,
            sincronizar_ccl,
            sincronizar_dolar_oficial,
            sincronizar_mep,
        )
        from app.servicios.inflacion import sincronizar_inflacion
        from app.servicios.bots.senales import evaluar_senales
        from app.servicios.reparador import reparar_todo

        try:
            conexion = obtener_conexion()  # cada thread necesita su conexión
            try:
                resumen = sincronizar_todo(conexion)
                resumen["reparacion"] = reparar_todo(conexion)
                # El dólar depende de las velas ya sincronizadas y reparadas
                resumen["ccl"] = sincronizar_ccl(conexion)
                generar_velas_ccl(conexion)
                resumen["mep"] = sincronizar_mep(conexion)
                resumen["inflacion"] = sincronizar_inflacion(conexion)
                resumen["dolar_oficial"] = sincronizar_dolar_oficial(conexion)
                # Con los datos al día, los bots activos miran su última barra
                resumen["senales"] = evaluar_senales(conexion)
                _ultimo_resumen = resumen
            finally:
                conexion.close()
        finally:
            _lock_sync.release()

    threading.Thread(target=_correr, name="sync-mop", daemon=True).start()
    return True
