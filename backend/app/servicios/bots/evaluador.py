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
from app.servicios.bots.alineacion import ORDEN_TEMPORALIDADES, alinear_sobre_base
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
    """Una corrida de `calcular` por (indicador, temporalidad, params): las
    condiciones que comparten indicador (k cruza d, media y z de las mismas
    bandas) no recalculan.

    Confluencia: cada condición se calcula sobre las velas de SU temporalidad,
    con la EMA central de esa ventana (D=200, S=50, M=12), y si es superior a la
    del bot se alinea sobre el índice base sin lookahead (ver alineacion.py).
    """

    def __init__(self, velas_por: dict[str, list[dict]], temporalidad_base: str):
        self._velas_por = velas_por
        self._base = temporalidad_base
        self._ts_base = [v["ts"] for v in velas_por[temporalidad_base]]
        self._series: dict[tuple, dict[str, list]] = {}

    def serie(self, indicador: str, nombre: str, params: dict | None, temporalidad: str) -> list:
        if ORDEN_TEMPORALIDADES[temporalidad] < ORDEN_TEMPORALIDADES[self._base]:
            raise ValueError(
                f"Una condición {temporalidad} no puede evaluarse en un bot {self._base}: "
                "la temporalidad de la condición debe ser igual o superior a la del bot"
            )
        efectivos = _params_de(params, indicador, temporalidad)
        clave = (indicador, temporalidad, tuple(sorted(efectivos.items())))
        if clave not in self._series:
            velas = self._velas_por[temporalidad]
            series = calcular(indicador, velas, **efectivos)
            if temporalidad != self._base:
                ts_superior = [v["ts"] for v in velas]
                series = {
                    n: alinear_sobre_base(self._ts_base, ts_superior, s, temporalidad)
                    for n, s in series.items()
                }
            self._series[clave] = series
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
    condicion: Condicion, cache: _CacheSeries, cierres: list[float], temporalidad_bot: str
) -> list[bool]:
    temporalidad = condicion.temporalidad or temporalidad_bot
    serie = cache.serie(condicion.indicador, condicion.serie, condicion.params, temporalidad)

    if condicion.operador in ("cruza_arriba_precio", "cruza_abajo_precio"):
        # El precio (cierre de la temporalidad del BOT) es quien cruza la serie
        operador = condicion.operador.replace("_precio", "")
        return _comparar(operador, cierres, serie)

    if isinstance(condicion.objetivo, ObjetivoSerie):
        objetivo = cache.serie(
            condicion.indicador,
            condicion.objetivo.serie,
            condicion.objetivo.params or condicion.params,
            temporalidad,
        )
    else:
        objetivo = [condicion.objetivo] * len(serie)
    return _comparar(condicion.operador, serie, objetivo)


def _combinar_and(vectores: list[list[bool]], largo: int) -> list[bool]:
    """AND barra a barra; sin condiciones no hay señal (un bloque vacío no dispara)."""
    if not vectores:
        return [False] * largo
    return [all(v[i] for v in vectores) for i in range(largo)]


def temporalidades_de(reglas: Reglas, temporalidad_bot: str) -> set:
    """Las temporalidades que las reglas necesitan (para buscar sus velas)."""
    condiciones = [*reglas.entrada, *reglas.salida, *reglas.filtros]
    return {temporalidad_bot} | {c.temporalidad for c in condiciones if c.temporalidad}


def evaluar_reglas(velas_por: dict[str, list[dict]], reglas: Reglas, temporalidad: str) -> dict:
    """Evalúa las reglas sobre el índice de la temporalidad del bot.

    `velas_por` trae las velas de cada temporalidad que usan las condiciones
    (al menos la del bot). Devuelve `{"ts_entrada": [...], "ts_salida": [...]}`
    — ts de las barras base (las mismas que dibuja el chart) donde TODAS las
    condiciones del bloque se cumplen.
    """
    velas = velas_por[temporalidad]
    cache = _CacheSeries(velas_por, temporalidad)
    cierres = [v["cierre"] for v in velas]
    ts = [v["ts"] for v in velas]

    entrada = _combinar_and(
        [
            _evaluar_condicion(c, cache, cierres, temporalidad)
            for c in [*reglas.entrada, *reglas.filtros]
        ],
        len(velas),
    ) if reglas.entrada else [False] * len(velas)
    salida = _combinar_and(
        [_evaluar_condicion(c, cache, cierres, temporalidad) for c in reglas.salida],
        len(velas),
    )

    return {
        "ts_entrada": [t for t, ok in zip(ts, entrada) if ok],
        "ts_salida": [t for t, ok in zip(ts, salida) if ok],
    }


def _valor_serie(serie: list, i: int):
    valor = serie[i]
    return None if valor is None else round(float(valor), 4)


def detalle_entrada(
    velas_por: dict[str, list[dict]], reglas: Reglas, temporalidad: str, indice: int = -1
) -> list[dict]:
    """Desglose de cada condición de entrada+filtros en una barra concreta.

    Devuelve, por condición, su valor y su objetivo en esa barra y si se cumple:
    lo que explica POR QUÉ (no) dispara la señal ('estaba en z=−2,3, por eso…').
    """
    velas = velas_por[temporalidad]
    if not velas:
        return []
    i = indice if indice >= 0 else len(velas) + indice
    cache = _CacheSeries(velas_por, temporalidad)
    cierres = [v["cierre"] for v in velas]

    detalles = []
    for condicion in [*reglas.entrada, *reglas.filtros]:
        tf = condicion.temporalidad or temporalidad
        serie = cache.serie(condicion.indicador, condicion.serie, condicion.params, tf)
        cumple = _evaluar_condicion(condicion, cache, cierres, temporalidad)[i]

        objetivo_valor = None
        objetivo_serie = None
        if condicion.operador in ("cruza_arriba_precio", "cruza_abajo_precio"):
            valor = _valor_serie(cierres, i)  # el precio es el sujeto que cruza
            objetivo_valor = _valor_serie(serie, i)
        else:
            valor = _valor_serie(serie, i)
            if isinstance(condicion.objetivo, ObjetivoSerie):
                objetivo_serie = condicion.objetivo.serie
                obj = cache.serie(
                    condicion.indicador,
                    condicion.objetivo.serie,
                    condicion.objetivo.params or condicion.params,
                    tf,
                )
                objetivo_valor = _valor_serie(obj, i)
            else:
                objetivo_valor = condicion.objetivo

        detalles.append(
            {
                "indicador": condicion.indicador,
                "serie": condicion.serie,
                "temporalidad": tf,
                "operador": condicion.operador,
                "params": condicion.params,
                "valor": valor,
                "objetivo": objetivo_valor,
                "objetivo_serie": objetivo_serie,
                "cumple": bool(cumple),
            }
        )
    return detalles
