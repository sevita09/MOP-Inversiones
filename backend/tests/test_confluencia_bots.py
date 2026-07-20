"""Test punta a punta de la Triple Confluencia MOP (ESTRATEGIAS_BOTS, bot 1):
z mensual < −2 ∧ z semanal < −2 ∧ estocástico %K cruza arriba de %D en diario.

Serie sintética con historia conocida: dos años y medio planos alrededor de 100
(el warmup de las EMAs centrales S=50 y M=12), un derrumbe de 100→55 y una fase
baja oscilante donde el estocástico diario gira varias veces. Las señales solo
pueden aparecer DESPUÉS de que la primera vela mensual del derrumbe cerró: la
confluencia mensual mira velas cerradas, no la vela en curso.
"""
import math
from datetime import datetime, timedelta, timezone

from app.esquemas.reglas import Reglas
from app.servicios.bots.alineacion import clave_periodo
from app.servicios.bots.evaluador import evaluar_reglas

DIAS_WARMUP = 600
DIAS_DERRUMBE = 40
DIAS_FASE_BAJA = 150


def _cierres_sinteticos():
    plano = [100 + math.sin(i / 3) for i in range(DIAS_WARMUP)]
    derrumbe = [100 - (45 * (i + 1) / DIAS_DERRUMBE) for i in range(DIAS_DERRUMBE)]
    fase_baja = [55 + 2 * math.sin(i / 3) for i in range(DIAS_FASE_BAJA)]
    return plano + derrumbe + fase_baja


def _velas_diarias():
    cierres = _cierres_sinteticos()
    velas = []
    fecha = datetime(2021, 1, 4, tzinfo=timezone.utc)  # lunes
    for cierre in cierres:
        while fecha.weekday() >= 5:
            fecha += timedelta(days=1)
        velas.append(
            {
                "ts": int(fecha.timestamp()),
                "apertura": cierre,
                "maximo": cierre + 1,
                "minimo": cierre - 1,
                "cierre": cierre,
                "volumen": 1000,
            }
        )
        fecha += timedelta(days=1)
    return velas


def _agrupar(velas_diarias, temporalidad):
    """Velas S/M desde las diarias (incluida la última, 'en curso')."""
    grupos: dict = {}
    for vela in velas_diarias:
        grupos.setdefault(clave_periodo(vela["ts"], temporalidad), []).append(vela)
    barras = []
    for clave in sorted(grupos):
        del_periodo = grupos[clave]
        barras.append(
            {
                "ts": del_periodo[0]["ts"],
                "apertura": del_periodo[0]["apertura"],
                "maximo": max(v["maximo"] for v in del_periodo),
                "minimo": min(v["minimo"] for v in del_periodo),
                "cierre": del_periodo[-1]["cierre"],
                "volumen": sum(v["volumen"] for v in del_periodo),
            }
        )
    return barras


TRIPLE_CONFLUENCIA = Reglas(
    version=1,
    entrada=[
        {"indicador": "bandas", "serie": "z", "temporalidad": "M", "operador": "menor", "objetivo": -2},
        {"indicador": "bandas", "serie": "z", "temporalidad": "S", "operador": "menor", "objetivo": -2},
        {"indicador": "estocastico", "serie": "k", "operador": "cruza_arriba", "objetivo": {"serie": "d"}},
    ],
    salida=[
        {"indicador": "bandas", "serie": "z", "temporalidad": "S", "operador": "mayor", "objetivo": 0}
    ],
    filtros=[],
)


def test_triple_confluencia_dispara_tras_el_derrumbe_sin_lookahead():
    velas_d = _velas_diarias()
    velas_por = {"D": velas_d, "S": _agrupar(velas_d, "S"), "M": _agrupar(velas_d, "M")}

    resultado = evaluar_reglas(velas_por, TRIPLE_CONFLUENCIA, "D")
    entradas = resultado["ts_entrada"]

    assert len(entradas) > 0, "el derrumbe tiene que disparar la confluencia"

    inicio_derrumbe = velas_d[DIAS_WARMUP]["ts"]
    assert all(ts > inicio_derrumbe for ts in entradas)

    # Sin lookahead punta a punta: el z mensual < −2 recién existe cuando cerró
    # la primera vela mensual del derrumbe → ninguna señal en ese mismo mes
    mes_del_derrumbe = clave_periodo(inicio_derrumbe, "M")
    assert all(clave_periodo(ts, "M") > mes_del_derrumbe for ts in entradas)


def test_sin_la_condicion_mensual_dispara_antes():
    """La condición M recorta señales (AND): sacarla solo puede agregar fechas."""
    velas_d = _velas_diarias()
    velas_por = {"D": velas_d, "S": _agrupar(velas_d, "S"), "M": _agrupar(velas_d, "M")}

    sin_mensual = Reglas(
        version=1,
        entrada=[c for c in TRIPLE_CONFLUENCIA.entrada if c.temporalidad != "M"],
        salida=[],
        filtros=[],
    )
    completa = set(evaluar_reglas(velas_por, TRIPLE_CONFLUENCIA, "D")["ts_entrada"])
    relajada = set(evaluar_reglas(velas_por, sin_mensual, "D")["ts_entrada"])
    assert completa <= relajada
    assert len(relajada) >= len(completa)