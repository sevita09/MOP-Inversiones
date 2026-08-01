"""Correlación entre papeles: matriz y ventana móvil, sobre retornos."""
from datetime import datetime, timedelta, timezone

from app.repositorios import retornos as repo
from app.servicios.correlaciones import correlacion, matriz_correlacion, rolling

INICIO = datetime(2026, 1, 1, tzinfo=timezone.utc)


def _guardar(conexion, ticker, retornos, temporalidad="D", moneda="USD"):
    """Guarda una serie de retornos, una por rueda consecutiva."""
    repo.guardar(
        conexion,
        [
            {
                "ticker": ticker,
                "temporalidad": temporalidad,
                "moneda": moneda,
                "ts": int((INICIO + timedelta(days=i)).timestamp()),
                "retorno": valor,
            }
            for i, valor in enumerate(retornos)
        ],
    )


def _alternada(cantidad: int, signo: int = 1) -> list:
    """Serie que sube y baja alternando, para tener varianza real."""
    return [signo * (0.01 if i % 2 == 0 else -0.008) for i in range(cantidad)]


# --- el coeficiente ---


def test_una_serie_consigo_misma_da_uno():
    serie = _alternada(40)
    assert round(correlacion(serie, serie), 6) == 1.0


def test_una_serie_contra_su_opuesta_da_menos_uno():
    serie = _alternada(40)
    assert round(correlacion(serie, [-v for v in serie]), 6) == -1.0


def test_una_constante_no_correlaciona():
    """Sin varianza la fórmula dividiría por cero: no hay respuesta posible."""
    assert correlacion(_alternada(40), [0.01] * 40) is None


def test_series_de_distinto_largo_no_se_comparan():
    assert correlacion(_alternada(40), _alternada(20)) is None


# --- matriz ---


def test_la_diagonal_es_uno_y_la_matriz_es_simetrica(conexion):
    _guardar(conexion, "GGAL", _alternada(60))
    _guardar(conexion, "PAMP", _alternada(60, -1))

    resultado = matriz_correlacion(conexion, ["GGAL", "PAMP"])
    assert resultado["matriz"][0][0] == 1.0 and resultado["matriz"][1][1] == 1.0
    assert resultado["matriz"][0][1] == resultado["matriz"][1][0] == -1.0


def test_dos_papeles_que_se_mueven_igual_dan_uno(conexion):
    _guardar(conexion, "GGAL", _alternada(60))
    _guardar(conexion, "BMA", _alternada(60))

    resultado = matriz_correlacion(conexion, ["GGAL", "BMA"])
    assert resultado["matriz"][0][1] == 1.0


def test_solo_cuentan_las_fechas_donde_operaron_los_dos(conexion):
    """Si uno no tuvo rueda, ese día no dice nada sobre cómo se mueven juntos."""
    _guardar(conexion, "GGAL", _alternada(60))
    _guardar(conexion, "PAMP", _alternada(40))  # 20 ruedas menos

    resultado = matriz_correlacion(conexion, ["GGAL", "PAMP"])
    assert resultado["pares"][0][1] == 40


def test_con_pocos_datos_no_se_arriesga_un_numero(conexion):
    """Dos meses pueden dar 0,9 de casualidad: por debajo del mínimo, None."""
    _guardar(conexion, "GGAL", _alternada(10))
    _guardar(conexion, "PAMP", _alternada(10))

    resultado = matriz_correlacion(conexion, ["GGAL", "PAMP"])
    assert resultado["matriz"][0][1] is None
    assert resultado["pares"][0][1] == 10


def test_los_tickers_repetidos_se_colapsan(conexion):
    _guardar(conexion, "GGAL", _alternada(60))
    _guardar(conexion, "PAMP", _alternada(60))

    resultado = matriz_correlacion(conexion, ["GGAL", "ggal", "PAMP"])
    assert resultado["tickers"] == ["GGAL", "PAMP"]


def test_cada_moneda_tiene_su_matriz(conexion):
    """En pesos la devaluación es un factor común que infla la correlación."""
    _guardar(conexion, "GGAL", _alternada(60), moneda="USD")
    _guardar(conexion, "PAMP", _alternada(60, -1), moneda="USD")
    # En pesos las dos suben juntas: el mismo dólar de fondo
    _guardar(conexion, "GGAL", [0.01] * 30 + _alternada(30), moneda="ARS")
    _guardar(conexion, "PAMP", [0.01] * 30 + _alternada(30), moneda="ARS")

    assert matriz_correlacion(conexion, ["GGAL", "PAMP"], moneda="USD")["matriz"][0][1] == -1.0
    assert matriz_correlacion(conexion, ["GGAL", "PAMP"], moneda="ARS")["matriz"][0][1] == 1.0


# --- ventana móvil ---


def test_la_ventana_movil_recorre_la_serie(conexion):
    _guardar(conexion, "GGAL", _alternada(50))
    _guardar(conexion, "PAMP", _alternada(50))

    resultado = rolling(conexion, "GGAL", "PAMP", ventana=20)
    assert len(resultado["puntos"]) == 31  # 50 − 20 + 1
    assert all(p["correlacion"] == 1.0 for p in resultado["puntos"])
    assert resultado["correlacion_total"] == 1.0


def test_la_ventana_muestra_el_cambio_que_el_total_esconde(conexion):
    """Descorrelacionados y después pegados: el promedio no lo cuenta."""
    _guardar(conexion, "GGAL", _alternada(40) + _alternada(40))
    # La primera mitad va al revés, la segunda acompaña
    _guardar(conexion, "PAMP", _alternada(40, -1) + _alternada(40))

    resultado = rolling(conexion, "GGAL", "PAMP", ventana=20)
    assert resultado["puntos"][0]["correlacion"] == -1.0
    assert resultado["puntos"][-1]["correlacion"] == 1.0


def test_la_dispersion_son_las_ruedas_del_periodo(conexion):
    """La nube es la materia prima del tramo consultado, no de la ventana."""
    _guardar(conexion, "GGAL", _alternada(40))
    _guardar(conexion, "PAMP", _alternada(40))

    resultado = rolling(conexion, "GGAL", "PAMP", ventana=20)
    assert len(resultado["dispersion"]) == 40
    assert set(resultado["dispersion"][0]) == {"ts", "a", "b"}
    assert resultado["correlacion_ventana"] == resultado["puntos"][-1]["correlacion"]


def test_el_recorte_del_periodo_achica_todo(conexion):
    """Con `desde`, la línea y la nube muestran solo ese tramo."""
    _guardar(conexion, "GGAL", _alternada(80))
    _guardar(conexion, "PAMP", _alternada(80))
    desde = int((INICIO + timedelta(days=60)).timestamp())

    resultado = rolling(conexion, "GGAL", "PAMP", ventana=10, desde=desde)
    assert len(resultado["dispersion"]) == 20  # las últimas 20 ruedas
    # La línea arranca en la primera rueda del período, no una ventana después:
    # el calentamiento sale de la historia previa
    assert len(resultado["puntos"]) == 20
    assert resultado["puntos"][0]["ts"] == desde


def test_sin_historia_previa_la_linea_arranca_cuando_puede(conexion):
    """Si el período abarca todo lo que hay, no queda de dónde calentar."""
    _guardar(conexion, "GGAL", _alternada(30))
    _guardar(conexion, "PAMP", _alternada(30))

    resultado = rolling(conexion, "GGAL", "PAMP", ventana=10)
    assert len(resultado["puntos"]) == 21  # 30 − 10 + 1


def test_la_ventana_movil_coincide_con_el_calculo_directo(conexion):
    """Las sumas corridas tienen que dar lo mismo que Pearson por ventana."""
    import random

    random.seed(7)
    serie_a = [random.gauss(0, 0.02) for _ in range(120)]
    serie_b = [0.6 * v + random.gauss(0, 0.02) for v in serie_a]
    _guardar(conexion, "GGAL", serie_a)
    _guardar(conexion, "PAMP", serie_b)

    resultado = rolling(conexion, "GGAL", "PAMP", ventana=30)
    for indice, punto in enumerate(resultado["puntos"]):
        tramo = slice(indice, indice + 30)
        directo = correlacion(serie_a[tramo], serie_b[tramo])
        assert punto["correlacion"] == round(directo, 4)


def test_sin_historia_suficiente_no_hay_ventana(conexion):
    _guardar(conexion, "GGAL", _alternada(10))
    _guardar(conexion, "PAMP", _alternada(10))

    assert rolling(conexion, "GGAL", "PAMP", ventana=60)["puntos"] == []


# --- endpoints ---


def test_endpoint_de_matriz(cliente, conexion):
    _guardar(conexion, "GGAL", _alternada(60))
    _guardar(conexion, "PAMP", _alternada(60))

    datos = cliente.get("/api/analisis/correlaciones?tickers=GGAL,PAMP").json()
    assert datos["moneda"] == "USD"  # el default
    assert datos["matriz"][0][1] == 1.0

    assert cliente.get("/api/analisis/correlaciones?tickers=GGAL").status_code == 422
    assert cliente.get("/api/analisis/correlaciones?tickers=GGAL,NADA").status_code == 422
    assert cliente.get(
        "/api/analisis/correlaciones?tickers=GGAL,PAMP&temporalidad=H"
    ).status_code == 422


def test_endpoint_del_par(cliente, conexion):
    _guardar(conexion, "GGAL", _alternada(60))
    _guardar(conexion, "PAMP", _alternada(60))

    datos = cliente.get("/api/analisis/correlacion_par?a=GGAL&b=PAMP&ventana=30").json()
    assert datos["ventana"] == 30
    assert datos["correlacion_total"] == 1.0

    assert cliente.get(
        "/api/analisis/correlacion_par?a=GGAL&b=PAMP&ventana=5"
    ).status_code == 422
    # Una ventana de años enteros de ruedas es legítima
    assert cliente.get(
        "/api/analisis/correlacion_par?a=GGAL&b=PAMP&ventana=2500"
    ).status_code == 200
