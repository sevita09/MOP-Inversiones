import numpy as np
import pytest
from pydantic import ValidationError

from app.esquemas.reglas import SERIES_POR_INDICADOR, Reglas
from app.servicios.indicadores import calcular, disponibles


def _reglas(**bloques):
    base = {"version": 1, "entrada": [], "salida": [], "filtros": []}
    base.update(bloques)
    return Reglas(**base)


CONDICION_OK = {"indicador": "bandas", "serie": "z", "operador": "menor", "objetivo": -2}


def test_reglas_validas_de_la_metodologia():
    reglas = _reglas(
        entrada=[
            CONDICION_OK,
            {
                "indicador": "estocastico",
                "serie": "k",
                "operador": "cruza_arriba",
                "objetivo": {"serie": "d"},
            },
        ],
        salida=[{"indicador": "bandas", "serie": "media", "operador": "cruza_abajo_precio"}],
    )
    assert reglas.version == 1
    assert reglas.entrada[1].objetivo.serie == "d"
    assert reglas.salida[0].objetivo is None


def test_version_desconocida_es_invalida():
    with pytest.raises(ValidationError):
        Reglas(version=2, entrada=[], salida=[], filtros=[])


def test_indicador_desconocido_es_invalido():
    with pytest.raises(ValidationError, match="Indicador desconocido"):
        _reglas(entrada=[{**CONDICION_OK, "indicador": "magia"}])


def test_serie_inexistente_es_invalida():
    with pytest.raises(ValidationError, match="no tiene la serie"):
        _reglas(entrada=[{**CONDICION_OK, "serie": "w"}])


def test_operador_desconocido_es_invalido():
    with pytest.raises(ValidationError):
        _reglas(entrada=[{**CONDICION_OK, "operador": "igual"}])


def test_comparacion_sin_objetivo_es_invalida():
    with pytest.raises(ValidationError, match="necesita un objetivo"):
        _reglas(entrada=[{"indicador": "rsi", "serie": "rsi", "operador": "menor"}])


def test_cruce_de_precio_no_lleva_objetivo():
    with pytest.raises(ValidationError, match="no lleva objetivo"):
        _reglas(
            salida=[
                {
                    "indicador": "bandas",
                    "serie": "media",
                    "operador": "cruza_abajo_precio",
                    "objetivo": 5,
                }
            ]
        )


def test_objetivo_con_serie_de_otro_indicador_es_invalido():
    with pytest.raises(ValidationError, match="no es una serie de"):
        _reglas(
            entrada=[
                {
                    "indicador": "estocastico",
                    "serie": "k",
                    "operador": "cruza_arriba",
                    "objetivo": {"serie": "rsi"},
                }
            ]
        )


def test_temporalidad_por_condicion():
    reglas = _reglas(
        entrada=[
            {**CONDICION_OK, "temporalidad": "M"},
            {**CONDICION_OK, "temporalidad": "S"},
            CONDICION_OK,  # sin temporalidad: la del bot
        ]
    )
    assert reglas.entrada[0].temporalidad == "M"
    assert reglas.entrada[2].temporalidad is None


def test_temporalidad_horaria_es_invalida_en_condiciones():
    with pytest.raises(ValidationError):
        _reglas(entrada=[{**CONDICION_OK, "temporalidad": "H"}])


# --- validación de reglas incoherentes (v4.5) ---


def test_salida_sin_entrada_es_invalida():
    with pytest.raises(ValidationError, match="sin entrada no hay señal"):
        _reglas(salida=[CONDICION_OK])


def test_todo_vacio_es_valido():
    assert _reglas().entrada == []


def test_umbral_imposible_es_invalido():
    with pytest.raises(ValidationError, match="Umbral imposible"):
        _reglas(
            entrada=[
                {"indicador": "estocastico", "serie": "k", "operador": "menor", "objetivo": -5}
            ]
        )
    with pytest.raises(ValidationError, match="Umbral imposible"):
        _reglas(entrada=[{**CONDICION_OK, "objetivo": -25}])


def test_cruce_de_una_serie_consigo_misma_es_invalido():
    with pytest.raises(ValidationError, match="consigo misma"):
        _reglas(
            entrada=[
                {
                    "indicador": "ema",
                    "serie": "ema",
                    "operador": "cruza_arriba",
                    "objetivo": {"serie": "ema"},
                }
            ]
        )


def test_cruce_de_la_misma_serie_con_otros_params_es_valido():
    reglas = _reglas(
        entrada=[
            {
                "indicador": "ema",
                "serie": "ema",
                "operador": "cruza_arriba",
                "params": {"periodo": 10},
                "objetivo": {"serie": "ema", "params": {"periodo": 30}},
            }
        ]
    )
    assert reglas.entrada[0].objetivo.params == {"periodo": 30}


def test_el_mapa_de_series_coincide_con_el_registry():
    """SERIES_POR_INDICADOR es estático: si el registry cambia, esto avisa."""
    rng = np.random.default_rng(42)
    cierres = 100 + rng.normal(0, 2, 60).cumsum()
    velas = [
        {
            "ts": i,
            "apertura": c,
            "maximo": c + 1,
            "minimo": c - 1,
            "cierre": c,
            "volumen": 1000,
        }
        for i, c in enumerate(cierres)
    ]
    assert set(SERIES_POR_INDICADOR) == set(disponibles())
    for indicador, series in SERIES_POR_INDICADOR.items():
        assert set(calcular(indicador, velas)) == set(series), indicador
