"""Evaluación de señales del día: tras cada sync, los bots activos miran su
última barra y, si la entrada dispara ahí, se persiste una señal.

El bot ve lo mismo que el chart (velas_para_vista + indicadores del registry),
igual que el preview. La unicidad por barra (repositorios/senales) garantiza que
la señal se dispare una sola vez aunque el sync corra cada 15 minutos.
"""
from __future__ import annotations

import sqlite3
from typing import Optional

from app.esquemas.reglas import Reglas
from app.repositorios import bots as repo_bots
from app.repositorios import senales as repo_senales
from app.servicios.bots.evaluador import detalle_entrada, evaluar_reglas, temporalidades_de
from app.servicios.dolar import velas_para_vista


def _velas_del_bot(conexion: sqlite3.Connection, bot: dict, reglas: Reglas) -> dict:
    return {
        tf: velas_para_vista(conexion, bot["ticker"], tf, bot["moneda"])
        for tf in temporalidades_de(reglas, bot["temporalidad"])
    }


def evaluar_senales(conexion: sqlite3.Connection) -> int:
    """Evalúa los bots activos sobre su última barra. Devuelve las señales nuevas."""
    nuevas = 0
    for bot in repo_bots.listar(conexion):
        if not bot["activo"]:
            continue
        reglas = Reglas(**bot["reglas"])
        if not reglas.entrada:
            continue  # sin entrada no hay señal que evaluar

        velas_por = _velas_del_bot(conexion, bot, reglas)
        velas_bot = velas_por.get(bot["temporalidad"]) or []
        if not velas_bot:
            continue

        resultado = evaluar_reglas(velas_por, reglas, bot["temporalidad"])
        ultimo_ts = velas_bot[-1]["ts"]
        # Solo la última barra: es "la señal de hoy", no toda la historia
        if ultimo_ts not in set(resultado["ts_entrada"]):
            continue

        detalle = {
            "bot": bot["nombre"],
            "temporalidad": bot["temporalidad"],
            "moneda": bot["moneda"],
            "cierre": velas_bot[-1]["cierre"],
            # Por qué disparó: cada condición con su valor en la barra del disparo
            "condiciones": detalle_entrada(velas_por, reglas, bot["temporalidad"]),
        }
        if repo_senales.guardar(conexion, bot["id"], bot["ticker"], ultimo_ts, "entrada", detalle):
            nuevas += 1
    return nuevas


def _entrada_vigente(conexion: sqlite3.Connection, bot_id: int) -> Optional[bool]:
    """¿La entrada del bot todavía se cumple en su última barra? None si no se
    puede saber (bot borrado o sin velas)."""
    bot = repo_bots.obtener(conexion, bot_id)
    if bot is None:
        return None
    reglas = Reglas(**bot["reglas"])
    if not reglas.entrada:
        return None
    velas_por = _velas_del_bot(conexion, bot, reglas)
    velas_bot = velas_por.get(bot["temporalidad"]) or []
    if not velas_bot:
        return None
    resultado = evaluar_reglas(velas_por, reglas, bot["temporalidad"])
    return velas_bot[-1]["ts"] in set(resultado["ts_entrada"])


def anotar_vigencia(conexion: sqlite3.Connection, senales: list[dict]) -> list[dict]:
    """Marca cada señal con `vigente` (la entrada sigue cumpliéndose hoy).
    Cachea por bot: varias señales del mismo bot comparten la evaluación."""
    cache: dict[int, Optional[bool]] = {}
    for senal in senales:
        bot_id = senal["bot_id"]
        if bot_id not in cache:
            cache[bot_id] = _entrada_vigente(conexion, bot_id)
        senal["vigente"] = cache[bot_id]
    return senales


def ids_vencidas(conexion: sqlite3.Connection, senales: list[dict]) -> list[int]:
    """Ids de las señales cuya entrada ya NO se cumple (vigente is False)."""
    return [s["id"] for s in anotar_vigencia(conexion, senales) if s["vigente"] is False]
