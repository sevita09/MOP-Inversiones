"""Alineado de series superiores (S/M) sobre el índice de una temporalidad menor.

La regla dura de la confluencia: **la vela superior solo cuenta cerrada**. El
sync escribe la vela semanal/mensual EN CURSO en la base (refrescar_velas_en_
curso), así que alinear "la última vela disponible" miraría el futuro: la vela
de esta semana ya sabe cómo viene la semana. Acá cada barra base ve la última
barra superior cuyo período TERMINÓ antes del período en que vive la barra base.

Ejemplo (base D, superior S): el viernes de la semana N ve la semana N−1; el
lunes de la semana N+1 recién ahí ve la semana N. La vela S/M en curso nunca
aparece, y agregar una barra en curso no cambia ninguna señal pasada.
"""
from __future__ import annotations

from datetime import datetime, timezone

ORDEN_TEMPORALIDADES = {"D": 0, "S": 1, "M": 2}


def clave_periodo(ts: int, temporalidad: str) -> tuple:
    """Período (comparable y creciente en el tiempo) al que pertenece un ts."""
    fecha = datetime.fromtimestamp(ts, tz=timezone.utc).date()
    if temporalidad == "S":
        iso = fecha.isocalendar()  # (año ISO, semana ISO, día)
        return (iso[0], iso[1])
    if temporalidad == "M":
        return (fecha.year, fecha.month)
    return (fecha.year, fecha.month, fecha.day)


def alinear_sobre_base(
    ts_base: list[int],
    ts_superior: list[int],
    valores_superior: list,
    temporalidad_superior: str,
) -> list:
    """Proyecta una serie superior sobre el índice base, sin lookahead.

    Para cada ts base devuelve el valor de la última barra superior cuyo período
    es ESTRICTAMENTE anterior al período (superior) de esa barra base; None si
    todavía no hay ninguna cerrada. Ambas listas de ts deben venir ordenadas.
    """
    claves_superior = [clave_periodo(t, temporalidad_superior) for t in ts_superior]
    resultado = []
    ultima_cerrada = -1
    for t in ts_base:
        clave_actual = clave_periodo(t, temporalidad_superior)
        while (
            ultima_cerrada + 1 < len(claves_superior)
            and claves_superior[ultima_cerrada + 1] < clave_actual
        ):
            ultima_cerrada += 1
        resultado.append(valores_superior[ultima_cerrada] if ultima_cerrada >= 0 else None)
    return resultado
