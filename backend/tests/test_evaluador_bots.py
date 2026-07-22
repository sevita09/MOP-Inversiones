"""Tests del evaluador con series sintéticas: los cierres se eligen para que
cada regla dispare en barras conocidas de antemano."""
from app.esquemas.reglas import Reglas
from app.servicios.bots.evaluador import evaluar_reglas


def _velas(cierres):
    return [
        {
            "ts": (i + 1) * 100,
            "apertura": c,
            "maximo": c + 1,
            "minimo": c - 1,
            "cierre": c,
            "volumen": 1000,
        }
        for i, c in enumerate(cierres)
    ]


def _velas_d(cierres):
    """Velas diarias empaquetadas como las recibe el evaluador multitemporal."""
    return {"D": _velas(cierres)}


def _reglas(entrada=None, salida=None, filtros=None):
    return Reglas(
        version=1, entrada=entrada or [], salida=salida or [], filtros=filtros or []
    )


# ema con periodo 1 es el cierre tal cual: ideal para probar operadores puros
EMA_ES_EL_CIERRE = {"indicador": "ema", "serie": "ema", "params": {"periodo": 1}}


def test_umbral_mayor():
    reglas = _reglas(entrada=[{**EMA_ES_EL_CIERRE, "operador": "mayor", "objetivo": 20}])
    resultado = evaluar_reglas(_velas_d([10, 25, 15, 30]), reglas, "D")
    assert resultado["ts_entrada"] == [200, 400]
    assert resultado["ts_salida"] == []


def test_cruce_de_constante_dispara_solo_al_cruzar():
    reglas = _reglas(
        entrada=[{**EMA_ES_EL_CIERRE, "operador": "cruza_arriba", "objetivo": 20}]
    )
    # Cruza en la barra 3 (15→25) y NO re-dispara mientras sigue arriba
    resultado = evaluar_reglas(_velas_d([10, 15, 25, 30, 18, 22]), reglas, "D")
    assert resultado["ts_entrada"] == [300, 600]


def test_cruce_abajo_de_constante():
    reglas = _reglas(
        entrada=[{**EMA_ES_EL_CIERRE, "operador": "mayor", "objetivo": 999}],
        salida=[{**EMA_ES_EL_CIERRE, "operador": "cruza_abajo", "objetivo": 20}],
    )
    resultado = evaluar_reglas(_velas_d([30, 25, 15, 10]), reglas, "D")
    assert resultado["ts_salida"] == [300]


def test_cruce_entre_series_del_mismo_indicador():
    # EMA rápida (el cierre) cruza arriba de la EMA lenta (periodo 5) en el salto
    reglas = _reglas(
        entrada=[
            {
                **EMA_ES_EL_CIERRE,
                "operador": "cruza_arriba",
                "objetivo": {"serie": "ema", "params": {"periodo": 5}},
            }
        ]
    )
    resultado = evaluar_reglas(_velas_d([10, 10, 10, 10, 50]), reglas, "D")
    assert resultado["ts_entrada"] == [500]


def test_precio_cruza_abajo_una_serie():
    # SMA(3) de bollinger: en la barra 4 el cierre (4) cae bajo la media (8)
    reglas = _reglas(
        entrada=[{**EMA_ES_EL_CIERRE, "operador": "mayor", "objetivo": 999}],
        salida=[
            {
                "indicador": "bollinger",
                "serie": "media",
                "operador": "cruza_abajo_precio",
                "params": {"periodo": 3},
            }
        ],
    )
    resultado = evaluar_reglas(_velas_d([10, 10, 10, 4]), reglas, "D")
    assert resultado["ts_salida"] == [400]


def test_warmup_no_dispara():
    # bandas con periodo 3: las dos primeras barras no tienen σ → z es None.
    # La condición "z < 9" es siempre cierta una vez que el z existe: si alguna
    # de las dos primeras disparara, el warmup estaría contando.
    reglas = _reglas(
        entrada=[
            {
                "indicador": "bandas",
                "serie": "z",
                "operador": "menor",
                "objetivo": 9,
                "params": {"periodo": 3},
            }
        ]
    )
    resultado = evaluar_reglas(_velas_d([10, 12, 11, 13, 12]), reglas, "D")
    assert 100 not in resultado["ts_entrada"] and 200 not in resultado["ts_entrada"]
    assert len(resultado["ts_entrada"]) > 0


def test_and_de_condiciones():
    reglas = _reglas(
        entrada=[
            {**EMA_ES_EL_CIERRE, "operador": "mayor", "objetivo": 20},
            {**EMA_ES_EL_CIERRE, "operador": "menor", "objetivo": 28},
        ]
    )
    # Solo la barra 25 cumple ambas (30 falla la segunda, 10 la primera)
    resultado = evaluar_reglas(_velas_d([10, 25, 30]), reglas, "D")
    assert resultado["ts_entrada"] == [200]


def test_filtros_van_and_con_la_entrada():
    entrada = [{**EMA_ES_EL_CIERRE, "operador": "mayor", "objetivo": 20}]
    filtro_imposible = [{**EMA_ES_EL_CIERRE, "operador": "menor", "objetivo": 0}]
    con_filtro = _reglas(entrada=entrada, filtros=filtro_imposible)
    assert evaluar_reglas(_velas_d([25, 30]), con_filtro, "D")["ts_entrada"] == []


def test_entrada_vacia_nunca_dispara():
    # Un bot recién creado (todo vacío) no dispara nada
    resultado = evaluar_reglas(_velas_d([10, 20]), _reglas(), "D")
    assert resultado["ts_entrada"] == []
    assert resultado["ts_salida"] == []


def test_periodo_central_por_temporalidad():
    # En M la EMA central es 12: con 15 barras el z existe; en D (200) no llega
    condicion = {"indicador": "bandas", "serie": "z", "operador": "menor", "objetivo": 9}
    cierres = [10 + (i % 3) for i in range(15)]
    en_mensual = evaluar_reglas({"M": _velas(cierres)}, _reglas(entrada=[condicion]), "M")
    en_diario = evaluar_reglas(_velas_d(cierres), _reglas(entrada=[condicion]), "D")
    assert len(en_mensual["ts_entrada"]) > 0
    assert en_diario["ts_entrada"] == []
