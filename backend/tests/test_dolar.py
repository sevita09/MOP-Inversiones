from app.repositorios.tasas_dolar import (
    CCL,
    OFICIAL,
    guardar_tasas,
    obtener_tasa_en_fecha,
    obtener_tasas,
)
from app.repositorios.velas import guardar_velas, obtener_velas
from app.servicios.dolar import (
    calcular_ccl_diario,
    convertir_velas_a_usd,
    generar_velas_ccl,
    resamplear,
    se_convierte_a_usd,
    sincronizar_ccl,
)

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


# --- endpoint /api/dolar ---


def test_endpoint_dolar_devuelve_la_ultima_cotizacion(cliente, conexion):
    guardar_tasas(
        conexion,
        [
            {"fecha": "2026-06-10", "tipo": CCL, "valor": 1450.0},
            {"fecha": "2026-06-12", "tipo": CCL, "valor": 1488.4},
            {"fecha": "2026-06-11", "tipo": OFICIAL, "valor": 1428.5},
        ],
    )
    datos = cliente.get("/api/dolar").json()
    assert datos["ccl"]["valor"] == 1488.4
    assert datos["ccl"]["fecha"] == "2026-06-12"
    assert datos["oficial"]["valor"] == 1428.5


def test_endpoint_dolar_sin_datos_devuelve_nulos(cliente):
    datos = cliente.get("/api/dolar").json()
    assert datos == {"ccl": None, "mep": None, "oficial": None}


# --- velas sintéticas DOLARCCL ---


def test_genera_velas_ccl_desde_las_tasas(conexion):
    guardar_tasas(
        conexion,
        [
            {"fecha": "2026-06-10", "tipo": CCL, "valor": 1488.4},
            {"fecha": "2026-06-11", "tipo": CCL, "valor": 1495.0},
        ],
    )
    assert generar_velas_ccl(conexion) == 2  # devuelve las diarias guardadas
    velas = obtener_velas(conexion, "DOLARCCL", "D")
    primera = velas[0]
    assert primera["apertura"] == primera["maximo"] == primera["minimo"] == primera["cierre"] == 1488.4


def test_genera_velas_ccl_tambien_en_semanal_y_mensual(conexion):
    # Dos días de la misma semana (mié 10 y jue 11 de junio 2026) y mismo mes
    guardar_tasas(
        conexion,
        [
            {"fecha": "2026-06-10", "tipo": CCL, "valor": 1480.0},
            {"fecha": "2026-06-11", "tipo": CCL, "valor": 1495.0},
        ],
    )
    generar_velas_ccl(conexion)
    semanal = obtener_velas(conexion, "DOLARCCL", "S")
    mensual = obtener_velas(conexion, "DOLARCCL", "M")
    assert len(semanal) == 1  # ambos días caen en la misma semana
    assert semanal[0]["apertura"] == 1480.0  # primer día
    assert semanal[0]["cierre"] == 1495.0    # último día
    assert semanal[0]["maximo"] == 1495.0
    assert len(mensual) == 1
    assert mensual[0]["cierre"] == 1495.0


# --- resampleo ---


def vela_d(ts, valor):
    return {
        "ticker": "DOLARCCL",
        "temporalidad": "D",
        "ts": ts,
        "apertura": valor,
        "maximo": valor,
        "minimo": valor,
        "cierre": valor,
        "volumen": 0.0,
    }


def test_resamplea_semanal_agrupa_por_semana():
    # lunes 8, martes 9, y lunes 15 de junio 2026 (dos semanas)
    lun8 = int(__import__("datetime").datetime(2026, 6, 8, tzinfo=__import__("datetime").timezone.utc).timestamp())
    mar9 = lun8 + UN_DIA
    lun15 = lun8 + 7 * UN_DIA
    velas = resamplear([vela_d(lun8, 100), vela_d(mar9, 110), vela_d(lun15, 120)], "DOLARCCL", "S")
    assert len(velas) == 2
    assert velas[0]["apertura"] == 100 and velas[0]["cierre"] == 110 and velas[0]["maximo"] == 110
    assert velas[1]["apertura"] == 120


def test_resamplea_mensual_toma_ohlc_del_mes():
    import datetime as dt
    def ts(y, m, d):
        return int(dt.datetime(y, m, d, tzinfo=dt.timezone.utc).timestamp())
    velas = resamplear(
        [vela_d(ts(2026, 6, 1), 100), vela_d(ts(2026, 6, 15), 130), vela_d(ts(2026, 6, 30), 90),
         vela_d(ts(2026, 7, 1), 95)],
        "DOLARCCL", "M",
    )
    assert len(velas) == 2
    junio = velas[0]
    assert junio["apertura"] == 100 and junio["maximo"] == 130 and junio["minimo"] == 90 and junio["cierre"] == 90


# --- conversión a USD ---


def vela_precio(ticker, ts, cierre):
    return {
        "ticker": ticker,
        "temporalidad": "D",
        "ts": ts,
        "apertura": cierre,
        "maximo": cierre + 50,
        "minimo": cierre - 50,
        "cierre": cierre,
        "volumen": 100.0,
    }


def test_se_convierte_solo_byma():
    assert se_convierte_a_usd("GGAL")
    assert not se_convierte_a_usd("AAPL")
    assert not se_convierte_a_usd("DOLARCCL")


def test_convierte_dividiendo_por_la_tasa_del_dia(conexion):
    guardar_tasas(conexion, [{"fecha": "1970-01-02", "tipo": CCL, "valor": 1000.0}])
    velas = [vela_precio("GGAL", UN_DIA, 8000.0)]
    usd = convertir_velas_a_usd(conexion, "GGAL", velas)
    assert usd[0]["cierre"] == 8.0
    assert usd[0]["maximo"] == round(8050.0 / 1000, 4)


def test_convierte_usa_la_tasa_vigente_en_feriado(conexion):
    guardar_tasas(
        conexion,
        [
            {"fecha": "1970-01-02", "tipo": CCL, "valor": 1000.0},
            {"fecha": "1970-01-05", "tipo": CCL, "valor": 1100.0},
        ],
    )
    # ts del 1970-01-04 (feriado): usa la tasa del 02
    velas = [vela_precio("GGAL", 3 * UN_DIA, 8000.0)]
    usd = convertir_velas_a_usd(conexion, "GGAL", velas)
    assert usd[0]["cierre"] == 8.0


def test_no_convierte_tickers_que_ya_estan_en_usd(conexion):
    guardar_tasas(conexion, [{"fecha": "1970-01-02", "tipo": CCL, "valor": 1000.0}])
    velas = [vela_precio("AAPL", UN_DIA, 200.0)]
    assert convertir_velas_a_usd(conexion, "AAPL", velas) == velas


def test_descarta_velas_anteriores_a_la_primera_tasa(conexion):
    guardar_tasas(conexion, [{"fecha": "2020-01-01", "tipo": CCL, "valor": 1000.0}])
    velas = [vela_precio("GGAL", UN_DIA, 8000.0)]  # 1970, mucho antes
    assert convertir_velas_a_usd(conexion, "GGAL", velas) == []


def test_convierte_sin_tasas_devuelve_vacio(conexion):
    velas = [vela_precio("GGAL", UN_DIA, 8000.0)]
    assert convertir_velas_a_usd(conexion, "GGAL", velas) == []
