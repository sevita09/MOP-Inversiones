import pytest

from app.servicios.indicadores import registro


def velas(cierres):
    return [
        {"ticker": "X", "temporalidad": "D", "ts": i, "apertura": c, "maximo": c,
         "minimo": c, "cierre": c, "volumen": 0.0}
        for i, c in enumerate(cierres)
    ]


def test_registrar_y_calcular_un_indicador():
    # El doble de la columna cierre, con el primer valor en warmup (NaN)
    def doble(df, factor=2):
        serie = df["cierre"] * factor
        serie.iloc[0] = float("nan")
        return {"doble": serie}

    registro.registrar("doble_test", doble, {"factor": 2})
    salida = registro.calcular("doble_test", velas([10, 20, 30]))
    assert salida == {"doble": [None, 40.0, 60.0]}


def test_params_default_se_pueden_pisar():
    registro.registrar("triple_test", lambda df, factor=3: {"v": df["cierre"] * factor}, {"factor": 3})
    assert registro.calcular("triple_test", velas([10]))["v"] == [30.0]
    assert registro.calcular("triple_test", velas([10]), factor=5)["v"] == [50.0]


def test_indicador_desconocido_levanta_keyerror():
    with pytest.raises(KeyError):
        registro.calcular("no_existe", velas([1, 2]))


def test_disponibles_lista_los_registrados():
    registro.registrar("zzz_test", lambda df: {"z": df["cierre"]})
    assert "zzz_test" in registro.disponibles()


def test_nan_e_infinito_se_serializan_como_none():
    def con_inf(df):
        serie = df["cierre"].astype(float).copy()
        serie.iloc[0] = float("inf")
        serie.iloc[1] = float("nan")
        return {"s": serie}

    registro.registrar("inf_test", con_inf)
    assert registro.calcular("inf_test", velas([1, 2, 3]))["s"] == [None, None, 3.0]
