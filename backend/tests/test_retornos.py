"""Retornos logarítmicos precalculados: la base de estacionalidad y correlaciones."""
import math
from datetime import datetime, timedelta, timezone

from app.repositorios import retornos as repo
from app.repositorios.tasas_dolar import guardar_tasas
from app.repositorios.velas import guardar_velas
from app.servicios.retornos import calcular, recalcular_serie, recalcular_todo

UN_DIA = 86400


def _ts(fecha: str) -> int:
    return int(datetime.strptime(fecha, "%Y-%m-%d").replace(tzinfo=timezone.utc).timestamp())


def _velas(conexion, ticker, desde, precios, faltantes=()):
    inicio = datetime.strptime(desde, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    guardar_velas(
        conexion,
        [
            {
                "ticker": ticker,
                "temporalidad": "D",
                "ts": int((inicio + timedelta(days=i)).timestamp()),
                "apertura": precio,
                "maximo": precio,
                "minimo": precio,
                "cierre": precio,
                "volumen": 100,
                "es_faltante": 1 if i in faltantes else 0,
            }
            for i, precio in enumerate(precios)
        ],
    )


def _serie(velas_precios, ticker="GGAL", temporalidad="D", moneda="ARS"):
    """Arma velas sueltas (sin base) para probar el cálculo puro."""
    return [
        {"ts": (i + 1) * UN_DIA, "cierre": precio, "es_faltante": 0}
        for i, precio in enumerate(velas_precios)
    ]


# --- cálculo ---


def test_el_retorno_es_el_logaritmo_del_cociente():
    retornos = calcular(_serie([100, 110]), "GGAL", "D", "ARS")
    assert len(retornos) == 1
    assert retornos[0]["retorno"] == round(math.log(1.1), 8)
    assert retornos[0]["ts"] == 2 * UN_DIA  # se ata a la vela de llegada


def test_los_logaritmicos_se_suman_en_el_tiempo():
    """La propiedad por la que se usan: el retorno del tramo es la suma."""
    retornos = calcular(_serie([100, 110, 121]), "GGAL", "D", "ARS")
    total = sum(r["retorno"] for r in retornos)
    assert round(total, 8) == round(math.log(121 / 100), 8)


def test_subir_y_bajar_lo_mismo_vuelve_a_cero():
    retornos = calcular(_serie([100, 200, 100]), "GGAL", "D", "ARS")
    assert round(sum(r["retorno"] for r in retornos), 8) == 0.0


def test_una_vela_faltante_no_genera_retorno():
    """Un placeholder no es un precio que existió: no se inventa el salto."""
    velas = _serie([100, 110, 121])
    velas[1]["es_faltante"] = 1

    retornos = calcular(velas, "GGAL", "D", "ARS")
    assert len(retornos) == 1
    # El único retorno va del 100 al 121, saltando la faltante, y se ata al final
    assert retornos[0]["ts"] == 3 * UN_DIA
    assert retornos[0]["retorno"] == round(math.log(1.21), 8)


def test_una_serie_de_una_vela_no_tiene_retornos():
    assert calcular(_serie([100]), "GGAL", "D", "ARS") == []


def test_los_precios_invalidos_se_descartan():
    velas = _serie([100, 0, 110])
    assert len(calcular(velas, "GGAL", "D", "ARS")) == 1


# --- persistencia y actualización ---


def test_recalcular_guarda_la_serie(conexion):
    _velas(conexion, "GGAL", "2026-01-05", [100, 110, 121])

    assert recalcular_serie(conexion, "GGAL", "D", "ARS") == 2
    serie = repo.obtener(conexion, "GGAL", "D", "ARS")
    assert [round(r["retorno"], 6) for r in serie] == [round(math.log(1.1), 6)] * 2


def test_la_actualizacion_es_incremental(conexion):
    """Tras un sync solo se calculan las velas nuevas, no diez años de historia."""
    _velas(conexion, "GGAL", "2026-01-05", [100, 110])
    assert recalcular_serie(conexion, "GGAL", "D", "ARS") == 1

    _velas(conexion, "GGAL", "2026-01-05", [100, 110, 121, 133.1])
    assert recalcular_serie(conexion, "GGAL", "D", "ARS") == 2  # solo las dos nuevas
    assert len(repo.obtener(conexion, "GGAL", "D", "ARS")) == 3


def test_recalcular_completo_rehace_todo(conexion):
    _velas(conexion, "GGAL", "2026-01-05", [100, 110, 121])
    recalcular_serie(conexion, "GGAL", "D", "ARS")
    assert recalcular_serie(conexion, "GGAL", "D", "ARS", completo=True) == 2


def test_en_usd_el_retorno_descuenta_el_dolar(conexion):
    """Si el precio y el dólar suben lo mismo, en dólares no pasó nada."""
    _velas(conexion, "COME", "2026-01-05", [100, 200])
    guardar_tasas(
        conexion,
        [
            {"fecha": "2026-01-05", "tipo": "CCL", "valor": 1000},
            {"fecha": "2026-01-06", "tipo": "CCL", "valor": 2000},
        ],
    )

    recalcular_serie(conexion, "COME", "D", "ARS")
    recalcular_serie(conexion, "COME", "D", "USD")
    assert round(repo.obtener(conexion, "COME", "D", "ARS")[0]["retorno"], 6) == round(
        math.log(2), 6
    )
    assert round(repo.obtener(conexion, "COME", "D", "USD")[0]["retorno"], 6) == 0.0


def test_recalcular_todo_recorre_el_universo(conexion):
    _velas(conexion, "GGAL", "2026-01-05", [100, 110])
    _velas(conexion, "PAMP", "2026-01-05", [50, 55])

    resumen = recalcular_todo(conexion)
    assert resumen["errores"] == []
    assert repo.contar(conexion) > 0
    assert len(repo.obtener(conexion, "PAMP", "D", "ARS")) == 1


# --- consultas cruzadas ---


def test_alineados_indexa_por_fecha(conexion):
    """La forma que necesitan las correlaciones: qué hizo cada papel ese día."""
    _velas(conexion, "GGAL", "2026-01-05", [100, 110, 121])
    _velas(conexion, "PAMP", "2026-01-05", [50, 45, 45])
    recalcular_serie(conexion, "GGAL", "D", "ARS")
    recalcular_serie(conexion, "PAMP", "D", "ARS")

    matriz = repo.alineados(conexion, ["GGAL", "PAMP"], "D", "ARS")
    assert len(matriz) == 2
    primera = matriz[_ts("2026-01-06")]
    assert set(primera) == {"GGAL", "PAMP"}
    assert primera["GGAL"] > 0 and primera["PAMP"] < 0


def test_alineados_omite_al_papel_que_no_opero(conexion):
    """Sin retorno ese día el papel no aparece: quien consulta decide qué hacer."""
    _velas(conexion, "GGAL", "2026-01-05", [100, 110, 121])
    _velas(conexion, "PAMP", "2026-01-05", [50, 55])
    recalcular_serie(conexion, "GGAL", "D", "ARS")
    recalcular_serie(conexion, "PAMP", "D", "ARS")

    matriz = repo.alineados(conexion, ["GGAL", "PAMP"], "D", "ARS")
    assert set(matriz[_ts("2026-01-07")]) == {"GGAL"}


def test_alineados_cruza_por_dia_no_por_hora(conexion):
    """Cada mercado cierra a su hora: BYMA 03:00 UTC, NYSE 04:00.

    Cruzando por ts exacto un papel local nunca encontraría pareja con un CEDEAR
    ni con la serie de un ADR, y la correlación entre mercados daría vacío.
    """
    repo.guardar(
        conexion,
        [
            {"ticker": "ALUA", "temporalidad": "D", "moneda": "USD",
             "ts": _ts("2026-01-06") + 3 * 3600, "retorno": 0.01},
            {"ticker": "AAPL", "temporalidad": "D", "moneda": "USD",
             "ts": _ts("2026-01-06") + 4 * 3600, "retorno": 0.02},
        ],
    )

    matriz = repo.alineados(conexion, ["ALUA", "AAPL"], "D", "USD")
    assert len(matriz) == 1  # la misma rueda, no dos
    fila = matriz[_ts("2026-01-06")]  # indexada a la medianoche del día
    assert fila == {"ALUA": 0.01, "AAPL": 0.02}


def test_alineados_sin_tickers_no_consulta(conexion):
    assert repo.alineados(conexion, [], "D", "ARS") == {}
