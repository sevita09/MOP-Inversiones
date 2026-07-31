"""Estacionalidad: el cuadro años×meses y la vista por día de la semana."""
import math
from datetime import datetime, timezone

from app.repositorios import retornos as repo
from app.servicios.estacionalidad import MESES, por_dia_semana, por_mes


def _ts(fecha: str) -> int:
    return int(datetime.strptime(fecha, "%Y-%m-%d").replace(tzinfo=timezone.utc).timestamp())


def _retornos(conexion, pares, temporalidad="M", ticker="GGAL", moneda="USD"):
    """Guarda retornos ya calculados: `pares` es [(fecha, variación %)]."""
    repo.guardar(
        conexion,
        [
            {
                "ticker": ticker,
                "temporalidad": temporalidad,
                "moneda": moneda,
                "ts": _ts(fecha),
                # Se guarda el logaritmo, que es lo que produce el servicio
                "retorno": math.log(1 + pct / 100),
            }
            for fecha, pct in pares
        ],
    )


# --- cuadro mensual ---


def test_cada_celda_es_el_retorno_de_ese_mes(conexion):
    _retornos(conexion, [("2025-03-01", 10), ("2026-03-01", -5)])

    cuadro = por_mes(conexion, "GGAL")
    assert cuadro["columnas"] == MESES
    assert cuadro["anios"] == [2025, 2026]  # el más viejo arriba, como una línea de tiempo
    marzo = MESES.index("Mar")
    assert cuadro["matriz"][0][marzo] == 10.0
    assert cuadro["matriz"][1][marzo] == -5.0
    # Los meses sin dato quedan vacíos, no en cero
    assert cuadro["matriz"][1][MESES.index("Ene")] is None


def test_el_total_del_anio_encadena_sus_meses(conexion):
    """Dos meses de +10% no son +20%: son +21%."""
    _retornos(conexion, [("2026-01-01", 10), ("2026-02-01", 10)])

    cuadro = por_mes(conexion, "GGAL")
    assert cuadro["totales_anio"] == [21.0]


def test_el_resumen_promedia_sobre_los_logaritmos(conexion):
    """+50% y −50% no promedian 0%: encadenados dan −13,4%."""
    _retornos(conexion, [("2025-06-01", 50), ("2026-06-01", -50)])

    junio = por_mes(conexion, "GGAL")["resumen"][MESES.index("Jun")]
    assert junio["casos"] == 2
    assert junio["promedio_pct"] == -13.4
    assert junio["positivos_pct"] == 50.0


def test_la_mediana_y_los_positivos_por_mes(conexion):
    _retornos(
        conexion,
        [("2024-09-01", 4), ("2025-09-01", -2), ("2026-09-01", 10)],
    )

    septiembre = por_mes(conexion, "GGAL")["resumen"][MESES.index("Sep")]
    assert septiembre["mediana_pct"] == 4.0
    assert septiembre["positivos_pct"] == 66.7
    assert septiembre["casos"] == 3


def test_un_mes_sin_historia_no_tiene_estadisticas(conexion):
    _retornos(conexion, [("2026-01-01", 5)])

    resumen = por_mes(conexion, "GGAL")["resumen"]
    assert resumen[MESES.index("Ene")]["casos"] == 1
    assert resumen[MESES.index("Dic")] == {
        "promedio_pct": None,
        "mediana_pct": None,
        "positivos_pct": None,
        "casos": 0,
    }


def test_sin_datos_el_cuadro_queda_vacio(conexion):
    cuadro = por_mes(conexion, "GGAL")
    assert cuadro["anios"] == [] and cuadro["matriz"] == []
    assert all(c["casos"] == 0 for c in cuadro["resumen"])


def test_cada_moneda_tiene_su_cuadro(conexion):
    _retornos(conexion, [("2026-01-01", 30)], moneda="ARS")
    _retornos(conexion, [("2026-01-01", 5)], moneda="USD")

    enero = MESES.index("Ene")
    assert por_mes(conexion, "GGAL", "ARS")["matriz"][0][enero] == 30.0
    assert por_mes(conexion, "GGAL", "USD")["matriz"][0][enero] == 5.0


# --- día de la semana ---


def test_la_celda_del_dia_es_el_promedio_no_la_suma(conexion):
    """Un año tiene ~50 lunes: sumarlos mediría cuántos hubo, no cómo fueron."""
    # 2026-01-05 y 2026-01-12 son lunes
    _retornos(conexion, [("2026-01-05", 2), ("2026-01-12", 4)], temporalidad="D")

    cuadro = por_dia_semana(conexion, "GGAL")
    lunes = cuadro["columnas"].index("Lun")
    assert cuadro["matriz"][0][lunes] == 3.0  # promedio de +2% y +4%
    assert cuadro["detalle"] == "retorno promedio del día"


def test_el_fin_de_semana_no_entra(conexion):
    # 2026-01-10 es sábado y 2026-01-11 domingo
    _retornos(
        conexion,
        [("2026-01-09", 1), ("2026-01-10", 99), ("2026-01-11", 99)],
        temporalidad="D",
    )

    cuadro = por_dia_semana(conexion, "GGAL")
    assert cuadro["columnas"] == ["Lun", "Mar", "Mié", "Jue", "Vie"]
    assert cuadro["matriz"][0][cuadro["columnas"].index("Vie")] == 1.0
    assert sum(1 for celda in cuadro["matriz"][0] if celda is not None) == 1


def test_el_resumen_por_dia_cuenta_todas_las_ruedas(conexion):
    _retornos(
        conexion,
        [("2025-01-06", 1), ("2026-01-05", 3), ("2026-01-12", -1)],
        temporalidad="D",
    )

    cuadro = por_dia_semana(conexion, "GGAL")
    lunes = cuadro["resumen"][cuadro["columnas"].index("Lun")]
    assert lunes["casos"] == 3  # las tres ruedas, no los dos años
    assert lunes["positivos_pct"] == 66.7


# --- endpoint ---


def test_endpoint_de_estacionalidad(cliente, conexion):
    _retornos(conexion, [("2026-05-01", 7)])

    datos = cliente.get("/api/analisis/estacionalidad?ticker=GGAL").json()
    assert datos["moneda"] == "USD"  # el default
    assert datos["matriz"][0][MESES.index("May")] == 7.0

    assert cliente.get("/api/analisis/estacionalidad?ticker=NADA").status_code == 422
    assert cliente.get(
        "/api/analisis/estacionalidad?ticker=GGAL&moneda=EUR"
    ).status_code == 422
    assert cliente.get(
        "/api/analisis/estacionalidad?ticker=GGAL&vista=hora"
    ).status_code == 422
    assert cliente.get(
        "/api/analisis/estacionalidad?ticker=GGAL&vista=dia_semana"
    ).json()["columnas"] == ["Lun", "Mar", "Mié", "Jue", "Vie"]
