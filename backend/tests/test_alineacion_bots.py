"""Tests del alineado sin lookahead: la vela superior solo cuenta CERRADA."""
from datetime import datetime, timedelta, timezone

from app.esquemas.reglas import Reglas
from app.servicios.bots.alineacion import alinear_sobre_base, clave_periodo
from app.servicios.bots.evaluador import evaluar_reglas


def _ts(anio, mes, dia):
    return int(datetime(anio, mes, dia, tzinfo=timezone.utc).timestamp())


def _dias_habiles(desde, cantidad):
    """ts diarios de lunes a viernes a partir de una fecha."""
    resultado = []
    fecha = desde
    while len(resultado) < cantidad:
        if fecha.weekday() < 5:
            resultado.append(int(fecha.replace(tzinfo=timezone.utc).timestamp()))
        fecha += timedelta(days=1)
    return resultado


# Lunes 2024-01-01, 2024-01-08 y 2024-01-15: tres semanas consecutivas
LUNES_1, LUNES_2, LUNES_3 = _ts(2024, 1, 1), _ts(2024, 1, 8), _ts(2024, 1, 15)


def test_cada_dia_ve_la_ultima_semana_cerrada():
    dias = _dias_habiles(datetime(2024, 1, 1), 12)  # 1-ene a 16-ene hábiles
    # Tres velas semanales: la de la semana 3 (15-ene) está EN CURSO ese lunes
    alineado = alinear_sobre_base(dias, [LUNES_1, LUNES_2, LUNES_3], [10, 20, 30], "S")
    # Toda la semana 1: sin semana cerrada previa
    assert alineado[:5] == [None] * 5
    # Toda la semana 2 (8-ene a 12-ene) ve la semana 1
    assert alineado[5:10] == [10] * 5
    # Lunes y martes de la semana 3 ven la semana 2 — la 3 en curso NUNCA aparece
    assert alineado[10:] == [20, 20]


def test_la_vela_mensual_en_curso_no_aparece():
    # Días de febrero: el valor mensual visible es el de enero, aunque la vela
    # de febrero (en curso) ya esté escrita en la base por el sync
    dias = _dias_habiles(datetime(2024, 2, 1), 5)
    meses = [_ts(2024, 1, 1), _ts(2024, 2, 1)]
    alineado = alinear_sobre_base(dias, meses, [100, 999], "M")
    assert alineado == [100] * 5


def test_agregar_una_barra_en_curso_no_cambia_senales_pasadas():
    def velas(ts_lista, cierres):
        return [
            {"ts": t, "apertura": c, "maximo": c + 1, "minimo": c - 1, "cierre": c, "volumen": 1}
            for t, c in zip(ts_lista, cierres)
        ]

    dias = _dias_habiles(datetime(2024, 1, 1), 12)
    velas_d = velas(dias, [10, 11, 10, 11, 10, 11, 10, 11, 10, 11, 10, 11])
    # ema(1) semanal = el cierre semanal tal cual; la semana 2 salta a 50
    semanas_cerradas = velas([LUNES_1, LUNES_2], [10, 50])
    con_en_curso = semanas_cerradas + velas([LUNES_3], [999])  # el sync escribió la semana 3

    reglas = Reglas(
        version=1,
        entrada=[
            {
                "indicador": "ema",
                "serie": "ema",
                "operador": "mayor",
                "objetivo": 20,
                "params": {"periodo": 1},
                "temporalidad": "S",
            }
        ],
        salida=[],
        filtros=[],
    )
    sin_barra = evaluar_reglas({"D": velas_d, "S": semanas_cerradas}, reglas, "D")
    con_barra = evaluar_reglas({"D": velas_d, "S": con_en_curso}, reglas, "D")
    # La semana 2 (cierre 50 > 20) se ve recién desde el lunes de la semana 3
    assert sin_barra["ts_entrada"] == dias[10:]
    # La barra en curso no agrega ni corre ninguna señal
    assert con_barra["ts_entrada"] == sin_barra["ts_entrada"]


def test_condicion_menor_a_la_del_bot_es_invalida():
    import pytest

    reglas = Reglas(
        version=1,
        entrada=[
            {
                "indicador": "ema",
                "serie": "ema",
                "operador": "mayor",
                "objetivo": 0,
                "temporalidad": "D",
            }
        ],
        salida=[],
        filtros=[],
    )
    velas_s = [{"ts": LUNES_1, "apertura": 1, "maximo": 2, "minimo": 0, "cierre": 1, "volumen": 1}]
    with pytest.raises(ValueError, match="igual o superior"):
        evaluar_reglas({"S": velas_s, "D": velas_s}, reglas, "S")


def test_clave_periodo_cruza_el_anio():
    # El 31-dic-2024 (martes) y el 2-ene-2025 caen en la MISMA semana ISO
    assert clave_periodo(_ts(2024, 12, 31), "S") == clave_periodo(_ts(2025, 1, 2), "S")
    # Pero en meses distintos
    assert clave_periodo(_ts(2024, 12, 31), "M") < clave_periodo(_ts(2025, 1, 2), "M")