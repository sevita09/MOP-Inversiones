"""Sync programado: la app se actualiza sola mientras está abierta.

En horario de rueda (lunes a viernes de 9 a 18, hora argentina) sincroniza
cada 15 minutos; fuera de la rueda, cada hora. El chequeo de versión nueva
viaja gratis: el frontend re-consulta /api/actualizacion con la misma cadencia.
"""
from __future__ import annotations

import threading
import time
from datetime import datetime
from typing import Optional
from zoneinfo import ZoneInfo

ZONA_ARGENTINA = ZoneInfo("America/Argentina/Buenos_Aires")
INTERVALO_RUEDA = 15 * 60
INTERVALO_FUERA = 60 * 60


def en_rueda(ahora: Optional[datetime] = None) -> bool:
    """True en horario bursátil argentino: lunes a viernes de 9 a 18."""
    momento = ahora or datetime.now(tz=ZONA_ARGENTINA)
    local = momento.astimezone(ZONA_ARGENTINA)
    return local.weekday() < 5 and 9 <= local.hour < 18


def proximo_intervalo(ahora: Optional[datetime] = None) -> int:
    """Segundos hasta el próximo sync según el horario."""
    return INTERVALO_RUEDA if en_rueda(ahora) else INTERVALO_FUERA


def iniciar_programador() -> None:
    """Lanza el loop de sync periódico en un thread daemon (muere con la app)."""

    def _correr():
        from app.servicios.sincronizador import sincronizar_en_background

        while True:
            time.sleep(proximo_intervalo())
            sincronizar_en_background()  # no hace nada si ya hay uno corriendo

    threading.Thread(target=_correr, name="programador-mop", daemon=True).start()
