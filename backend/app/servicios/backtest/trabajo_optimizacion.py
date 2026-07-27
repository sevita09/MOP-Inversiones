"""Corre la optimización en un thread aparte y expone su progreso.

Una grilla de cientos de backtests tarda; el frontend arranca el trabajo y va
consultando el avance. Una sola optimización a la vez (SQLite y CPU).
"""
from __future__ import annotations

import threading
from typing import Optional

from app.db import obtener_conexion
from app.servicios.backtest.optimizador import optimizar

_lock = threading.Lock()
_estado: dict = {
    "en_curso": False,
    "bot_id": None,
    "hechos": 0,
    "total": 0,
    "resultado": None,
    "error": None,
}


def estado_optimizacion() -> dict:
    return dict(_estado)


def hay_optimizacion_en_curso() -> bool:
    return _estado["en_curso"]


def lanzar_optimizacion(bot: dict, parametros: list[dict], metrica: str) -> bool:
    """Arranca la optimización en background. False si ya hay una corriendo."""
    if not _lock.acquire(blocking=False):
        return False

    _estado.update(
        {"en_curso": True, "bot_id": bot["id"], "hechos": 0, "total": 0,
         "resultado": None, "error": None}
    )

    def _correr():
        try:
            conexion = obtener_conexion()  # cada thread necesita su conexión
            try:
                def progreso(hechos: int, total: int) -> None:
                    _estado["hechos"] = hechos
                    _estado["total"] = total

                _estado["resultado"] = optimizar(
                    conexion, bot, parametros, metrica, progreso
                )
            finally:
                conexion.close()
        except Exception as error:
            _estado["error"] = str(error)
        finally:
            _estado["en_curso"] = False
            _lock.release()

    threading.Thread(target=_correr, name="optimizacion-mop", daemon=True).start()
    return True
