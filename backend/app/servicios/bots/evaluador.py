"""Evaluador de reglas de bots sobre las series del registry de indicadores.

Principio de la etapa v4: el bot ve LO MISMO que el chart. Acá no se recalcula
nada — las velas llegan de `velas_para_vista` (moneda y ADR ya resueltos) y las
series salen de `servicios/indicadores.calcular`, igual que `/api/indicadores`.

Cada condición produce un vector booleano por barra; las condiciones de un
bloque se combinan con AND (los filtros van AND con la entrada). El warmup de
un indicador (None) nunca cumple una condición: sin datos no hay señal.
"""
from __future__ import annotations

from app.config import periodo_ema_central
from app.esquemas.reglas import Condicion, ObjetivoSerie, Reglas
from app.servicios.indicadores import calcular, defaults_de

# El período de estos indicadores es la EMA central de la metodología: depende
# de la temporalidad y se inyecta acá (mismo criterio que routers/indicadores)
INDICADORES_EMA_CENTRAL = {"bandas", "percentil_distancia"}


def _params_de(condicion_params: dict | None, indicador: str, temporalidad: str) -> dict:
    """Los params efectivos: EMA central por temporalidad + overrides válidos."""
    params: dict = {}
    if indicador in INDICADORES_EMA_CENTRAL:
        params["periodo"] = periodo_ema_central(temporalidad)
    defaults = defaults_de(indicador)
    for clave, valor in (condicion_params or {}).items():
        if clave in defaults:
            params[clave] = type(defaults[clave])(valor)
    return params


class _CacheSeries:
    """Una corrida de `calcular` por (indicador, params): las condiciones que
    comparten indicador (k cruza d, media y z de las mismas bandas) no recalculan."""

    def __init__(self, velas: list[dict], temporalidad: str):
        self._velas = velas
        self._temporalidad = temporalidad
        self._series: dict[tuple, dict[str, list]] = {}

    def serie(self, indicador: str, nombre: str, params: dict | None) -> list:
        efectivos = _params_de(params, indicador, self._temporalidad)
        clave = (indicador, tuple(sorted(efectivos.items())))
        if clave not in self._series:
            self._series[clave] = calcular(indicador, self._velas, **efectivos)
        return self._series[clave][nombre]


def _comparar(operador: str, serie: list, objetivo: list) -> list[bool]:
    """Vector booleano de la condición; None (warmup) nunca cumple."""
    resultado = [False] * len(serie)
    for i in range(len(serie)):
        actual, obj = serie[i], objetivo[i]
        if actual is None or obj is None:
            continue
        if operador == "mayor":
            resultado[i] = actual > obj
        elif operador == "menor":
            resultado[i] = actual < obj
        else:  # cruces: necesitan la barra anterior completa
            if i == 0 or serie[i - 1] is None or objetivo[i - 1] is None:
                continue
            previa, obj_previa = serie[i - 1], objetivo[i - 1]
            if operador == "cruza_arriba":
                resultado[i] = previa <= obj_previa and actual > obj
            elif operador == "cruza_abajo":
                resultado[i] = previa >= obj_previa and actual < obj
    return resultado


def _evaluar_condicion(
    condicion: Condicion, cache: _CacheSeries, cierres: list[float]
) -> list[bool]:
    serie = cache.serie(condicion.indicador, condicion.serie, condicion.params)

    if condicion.operador in ("cruza_arriba_precio", "cruza_abajo_precio"):
        # El precio es quien cruza la serie: precio cruza_arriba serie
        operador = condicion.operador.replace("_precio", "")
        return _comparar(operador, cierres, serie)

    if isinstance(condicion.objetivo, ObjetivoSerie):
        objetivo = cache.serie(
            condicion.indicador,
            condicion.objetivo.serie,
            condicion.objetivo.params or condicion.params,
        )
    else:
        objetivo = [condicion.objetivo] * len(serie)
    return _comparar(condicion.operador, serie, objetivo)


def _combinar_and(vectores: list[list[bool]], largo: int) -> list[bool]:
    """AND barra a barra; sin condiciones no hay señal (un bloque vacío no dispara)."""
    if not vectores:
        return [False] * largo
    return [all(v[i] for v in vectores) for i in range(largo)]


def evaluar_reglas(velas: list[dict], reglas: Reglas, temporalidad: str) -> dict:
    """Evalúa las reglas sobre las velas y devuelve los ts donde disparan.

    `{"ts_entrada": [...], "ts_salida": [...]}` — ts de las barras (las mismas
    que dibuja el chart) donde TODAS las condiciones del bloque se cumplen.
    """
    cache = _CacheSeries(velas, temporalidad)
    cierres = [v["cierre"] for v in velas]
    ts = [v["ts"] for v in velas]

    entrada = _combinar_and(
        [_evaluar_condicion(c, cache, cierres) for c in [*reglas.entrada, *reglas.filtros]],
        len(velas),
    ) if reglas.entrada else [False] * len(velas)
    salida = _combinar_and(
        [_evaluar_condicion(c, cache, cierres) for c in reglas.salida], len(velas)
    )

    return {
        "ts_entrada": [t for t, ok in zip(ts, entrada) if ok],
        "ts_salida": [t for t, ok in zip(ts, salida) if ok],
    }
