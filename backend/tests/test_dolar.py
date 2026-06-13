from app.repositorios.tasas_dolar import (
    CCL,
    OFICIAL,
    guardar_tasas,
    obtener_tasa_en_fecha,
    obtener_tasas,
)
from app.repositorios.velas import guardar_velas
from app.servicios.dolar import calcular_ccl_diario, sincronizar_ccl

UN_DIA = 86400


def vela_ggal(ticker, ts, cierre, es_faltante=0):
    return {
        "ticker": ticker,
        "temporalidad": "D",
        "ts": ts,
        "apertura": cierre,
        "maximo": cierre,
        "minimo": cierre,
        "cierre": cierre,
        "volumen": 100.0,
        "es_faltante": es_faltante,
    }


def v(ts, cierre, faltante=0):
    return {"ts": ts, "cierre": cierre, "es_faltante": faltante}


# --- repositorio de tasas ---


def test_obtener_tasas_ordena_por_fecha(conexion):
    guardar_tasas(
        conexion,
        [
            {"fecha": "2026-06-10", "tipo": CCL, "valor": 1450.0},
            {"fecha": "2026-06-08", "tipo": CCL, "valor": 1400.0},
        ],
    )
    assert [t["fecha"] for t in obtener_tasas(conexion, CCL)] == ["2026-06-08", "2026-06-10"]


def test_tasa_en_fecha_exacta(conexion):
    guardar_tasas(conexion, [{"fecha": "2026-06-10", "tipo": CCL, "valor": 1450.0}])
    assert obtener_tasa_en_fecha(conexion, "2026-06-10") == 1450.0


def test_tasa_en_feriado_usa_el_dia_habil_anterior(conexion):
    guardar_tasas(
        conexion,
        [
            {"fecha": "2026-06-08", "tipo": CCL, "valor": 1400.0},
            {"fecha": "2026-06-10", "tipo": CCL, "valor": 1450.0},
        ],
    )
    assert obtener_tasa_en_fecha(conexion, "2026-06-09") == 1400.0  # feriado
    assert obtener_tasa_en_fecha(conexion, "2026-06-12") == 1450.0  # posterior


def test_tasa_anterior_al_primer_dato_es_none(conexion):
    guardar_tasas(conexion, [{"fecha": "2026-06-08", "tipo": CCL, "valor": 1400.0}])
    assert obtener_tasa_en_fecha(conexion, "2026-01-01") is None


def test_ccl_y_oficial_no_se_mezclan(conexion):
    guardar_tasas(
        conexion,
        [
            {"fecha": "2026-06-08", "tipo": CCL, "valor": 1450.0},
            {"fecha": "2026-06-08", "tipo": OFICIAL, "valor": 1000.0},
        ],
    )
    assert obtener_tasa_en_fecha(conexion, "2026-06-08", CCL) == 1450.0
    assert obtener_tasa_en_fecha(conexion, "2026-06-08", OFICIAL) == 1000.0


# --- cálculo de CCL ---


def test_ccl_aplica_la_formula_con_factor_diez():
    tasas = calcular_ccl_diario([v(UN_DIA, 8210.0)], [v(UN_DIA, 55.16)])
    assert len(tasas) == 1
    assert tasas[0]["valor"] == round(8210.0 * 10 / 55.16, 4)
    assert tasas[0]["tipo"] == CCL


def test_ccl_solo_en_fechas_con_ambos_lados():
    ars = [v(1 * UN_DIA, 8000.0), v(2 * UN_DIA, 8100.0)]
    adr = [v(1 * UN_DIA, 55.0)]  # falta el día 2
    tasas = calcular_ccl_diario(ars, adr)
    assert [t["fecha"] for t in tasas] == ["1970-01-02"]


def test_ccl_ignora_velas_faltantes_o_en_cero():
    ars = [v(1 * UN_DIA, 8000.0, faltante=1), v(2 * UN_DIA, 8100.0), v(3 * UN_DIA, 8200.0)]
    adr = [v(1 * UN_DIA, 55.0), v(2 * UN_DIA, 0.0), v(3 * UN_DIA, 55.5)]
    tasas = calcular_ccl_diario(ars, adr)
    # día 1: ARS faltante; día 2: ADR en cero; solo el día 3 sirve
    assert len(tasas) == 1
    assert tasas[0]["valor"] == round(8200.0 * 10 / 55.5, 4)


def test_ccl_ordena_por_fecha():
    ars = [v(3 * UN_DIA, 8200.0), v(1 * UN_DIA, 8000.0)]
    adr = [v(3 * UN_DIA, 55.5), v(1 * UN_DIA, 55.0)]
    tasas = calcular_ccl_diario(ars, adr)
    assert [t["fecha"] for t in tasas] == sorted(t["fecha"] for t in tasas)


# --- sincronización contra la base ---


def test_sincronizar_ccl_persiste_desde_las_velas(conexion):
    guardar_velas(
        conexion,
        [
            vela_ggal("GGAL", 1 * UN_DIA, 8000.0),
            vela_ggal("GGAL", 2 * UN_DIA, 8200.0),
            vela_ggal("GGALD", 1 * UN_DIA, 55.0),
            vela_ggal("GGALD", 2 * UN_DIA, 55.5),
        ],
    )
    assert sincronizar_ccl(conexion) == 2
    tasas = obtener_tasas(conexion, CCL)
    assert [t["valor"] for t in tasas] == [
        round(8000.0 * 10 / 55.0, 4),
        round(8200.0 * 10 / 55.5, 4),
    ]


def test_sincronizar_ccl_sin_datos_devuelve_cero(conexion):
    assert sincronizar_ccl(conexion) == 0
