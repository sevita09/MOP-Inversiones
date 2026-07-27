"""Grid search sobre uno o dos parámetros de un bot, con walk-forward.

Probar combinaciones hasta encontrar la que mejor rindió EN EL PASADO es la
forma más fácil de engañarse: siempre hay una que brilla por casualidad. Por eso
el optimizador:

- corre la grilla sobre el tramo de **optimización** (el 70% más viejo),
- valida la mejor combinación en el tramo de **validación** (el 30% final, que
  nunca vio), y
- avisa cuando los números huelen a sobreajuste (ver `evaluar_sobreajuste`).

Los parámetros optimizables apuntan a un lugar del bot:
- `{"tipo": "condicion", "bloque": "entrada", "indice": 0, "campo": "objetivo"}`
  (o `"campo": "params.periodo"`)
- `{"tipo": "riesgo", "campo": "stop_loss_pct"}`
cada uno con su rango `desde`/`hasta`/`paso`.
"""
from __future__ import annotations

import copy
import sqlite3
from typing import Optional

from app.servicios.backtest.simulador import correr_backtest

MAX_COMBINACIONES = 400  # techo de seguridad: una grilla enorme cuelga la app
METRICAS = ("retorno_pct", "sharpe", "profit_factor", "expectancy_pct")


def valores_de(param: dict) -> list[float]:
    """Los valores a probar de un parámetro, de `desde` a `hasta` cada `paso`."""
    desde, hasta, paso = param["desde"], param["hasta"], param["paso"]
    if paso <= 0 or hasta < desde:
        raise ValueError("Rango inválido: revisá desde, hasta y paso")
    valores = []
    actual = desde
    while actual <= hasta + 1e-9:
        valores.append(round(actual, 6))
        actual += paso
    return valores


def aplicar_valor(bot: dict, param: dict, valor: float) -> None:
    """Escribe el valor en el bot (que ya debe ser una copia)."""
    if param["tipo"] == "riesgo":
        bot.setdefault("riesgo", {})[param["campo"]] = valor
        return
    condicion = bot["reglas"][param["bloque"]][param["indice"]]
    campo = param["campo"]
    if campo.startswith("params."):
        clave = campo.split(".", 1)[1]
        condicion.setdefault("params", {})[clave] = valor
    else:
        condicion[campo] = valor


def _combinaciones(parametros: list[dict]) -> list[list[float]]:
    grillas = [valores_de(p) for p in parametros]
    if len(grillas) == 1:
        return [[v] for v in grillas[0]]
    return [[a, b] for a in grillas[0] for b in grillas[1]]


def corte_walk_forward(velas: list[dict], proporcion: float = 0.7) -> Optional[int]:
    """ts donde termina el tramo de optimización (70% de las barras)."""
    if len(velas) < 10:
        return None
    return velas[int(len(velas) * proporcion)]["ts"]


def _resultado_de(bot: dict, conexion, desde, hasta, metrica: str) -> dict:
    salida = correr_backtest(conexion, bot, desde, hasta)
    metricas = salida["estrategia"]["metricas"]
    valor = metricas.get(metrica)
    return {
        "metrica": None if valor is None else round(valor, 4),
        "retorno_pct": metricas["retorno_pct"],
        "trades": metricas["trades_total"],
        "drawdown_pct": metricas["drawdown_maximo_pct"],
        "buy_and_hold_pct": salida["buy_and_hold"]["metricas"]["retorno_pct"],
    }


def evaluar_sobreajuste(resultados: list[dict], mejor: dict, validacion: Optional[dict]) -> dict:
    """Señales de que el 'mejor' resultado puede ser casualidad, no una ventaja.

    - **Pocas operaciones**: con 5 trades cualquier número es ruido.
    - **Pico aislado**: si los vecinos de la mejor combinación rinden mucho peor,
      se optimizó una casualidad y no una zona robusta de parámetros.
    - **No valida**: la mejor combinación rinde mucho peor fuera de muestra.
    """
    avisos = []
    if mejor["trades"] < 10:
        avisos.append(
            f"Solo {mejor['trades']} operaciones: la muestra es chica para confiar en el resultado"
        )

    valores = sorted(
        (r["metrica"] for r in resultados if r["metrica"] is not None), reverse=True
    )
    if len(valores) >= 5:
        segundo_grupo = valores[1:4]
        promedio_vecinos = sum(segundo_grupo) / len(segundo_grupo)
        if valores[0] > 0 and promedio_vecinos < valores[0] * 0.5:
            avisos.append(
                "El mejor valor sobresale mucho de los demás: parece un pico aislado "
                "(la ventaja podría ser casualidad, no una zona robusta)"
            )

    if validacion is not None:
        dentro = mejor["retorno_pct"]
        fuera = validacion["retorno_pct"]
        if dentro > 0 and fuera <= 0:
            avisos.append(
                "En el período de validación (que la optimización no vio) la estrategia pierde: "
                "los parámetros están ajustados al pasado"
            )
        elif dentro > 0 and fuera < dentro * 0.3:
            avisos.append(
                "El rendimiento fuera de muestra es mucho peor que el optimizado: sospechá sobreajuste"
            )

    return {"hay_sobreajuste": bool(avisos), "avisos": avisos}


def optimizar(
    conexion: sqlite3.Connection,
    bot: dict,
    parametros: list[dict],
    metrica: str = "retorno_pct",
    progreso=None,
) -> dict:
    """Grid search + walk-forward. `progreso(hechos, total)` se llama por combinación."""
    if not 1 <= len(parametros) <= 2:
        raise ValueError("Se optimizan uno o dos parámetros por vez")
    if metrica not in METRICAS:
        raise ValueError(f"Métrica desconocida: {metrica} (usar {', '.join(METRICAS)})")

    combinaciones = _combinaciones(parametros)
    if len(combinaciones) > MAX_COMBINACIONES:
        raise ValueError(
            f"{len(combinaciones)} combinaciones es demasiado (máximo {MAX_COMBINACIONES}): "
            "agrandá el paso o achicá el rango"
        )

    # Corte walk-forward sobre las velas de la temporalidad del bot
    from app.servicios.backtest.cargador import cargar_historia

    _, _, velas_bot = cargar_historia(conexion, bot)
    corte = corte_walk_forward(velas_bot)

    resultados = []
    for hechos, valores in enumerate(combinaciones, start=1):
        candidato = copy.deepcopy(bot)
        for param, valor in zip(parametros, valores):
            aplicar_valor(candidato, param, valor)
        try:
            datos = _resultado_de(candidato, conexion, None, corte, metrica)
        except Exception:
            datos = {"metrica": None, "retorno_pct": 0.0, "trades": 0,
                     "drawdown_pct": 0.0, "buy_and_hold_pct": 0.0}
        resultados.append({"valores": valores, **datos})
        if progreso:
            progreso(hechos, len(combinaciones))

    con_metrica = [r for r in resultados if r["metrica"] is not None]
    if not con_metrica:
        return {
            "parametros": parametros, "metrica": metrica, "resultados": resultados,
            "mejor": None, "validacion": None,
            "sobreajuste": {"hay_sobreajuste": False, "avisos": ["Ninguna combinación operó"]},
        }

    mejor = max(con_metrica, key=lambda r: r["metrica"])

    # Validación: la mejor combinación sobre el tramo que la optimización NO vio
    validacion = None
    if corte is not None:
        candidato = copy.deepcopy(bot)
        for param, valor in zip(parametros, mejor["valores"]):
            aplicar_valor(candidato, param, valor)
        validacion = _resultado_de(candidato, conexion, corte, None, metrica)

    return {
        "parametros": parametros,
        "metrica": metrica,
        "corte_walk_forward": corte,
        "resultados": resultados,
        "mejor": mejor,
        "validacion": validacion,
        "sobreajuste": evaluar_sobreajuste(resultados, mejor, validacion),
    }
