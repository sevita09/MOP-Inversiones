from unittest.mock import patch

import app.servicios.reparador as reparador
from app.repositorios.velas import guardar_velas, obtener_velas
from app.servicios.reparador import (
    crear_placeholders,
    detectar_huecos,
    interpolar_faltantes,
    marcar_corruptas,
    redescargar_faltantes,
)

UN_DIA = 86400


def vela(ticker, ts, **campos):
    base = {
        "ticker": ticker,
        "temporalidad": "D",
        "ts": ts,
        "apertura": 100.0,
        "maximo": 101.0,
        "minimo": 99.0,
        "cierre": 100.0,
        "volumen": 10.0,
    }
    base.update(campos)
    return base


def cargar_calendario(conexion, tickers, dias):
    """Carga velas válidas para varios tickers en los días dados (calendario sintético)."""
    for ticker in tickers:
        guardar_velas(conexion, [vela(ticker, dia * UN_DIA) for dia in dias])


# --- marcado de precios en cero ---


def test_marca_velas_con_algun_precio_en_cero(conexion):
    guardar_velas(
        conexion,
        [
            vela("GGAL", 1 * UN_DIA),
            vela("GGAL", 2 * UN_DIA, cierre=0.0),
            vela("GGAL", 3 * UN_DIA, apertura=0.0),
            vela("GGAL", 4 * UN_DIA, maximo=-5.0),
        ],
    )
    assert marcar_corruptas(conexion) == 3
    flags = [v["es_faltante"] for v in obtener_velas(conexion, "GGAL", "D")]
    assert flags == [0, 1, 1, 1]


def test_marcar_corruptas_es_idempotente(conexion):
    guardar_velas(conexion, [vela("GGAL", UN_DIA, cierre=0.0)])
    assert marcar_corruptas(conexion) == 1
    assert marcar_corruptas(conexion) == 0


# --- detección de huecos ---


def test_detecta_hueco_contra_el_calendario_del_mercado(conexion):
    cargar_calendario(conexion, ["YPFD", "PAMP"], [1, 2, 3, 4, 5])
    guardar_velas(conexion, [vela("GGAL", d * UN_DIA) for d in (1, 2, 4, 5)])
    assert detectar_huecos(conexion, "GGAL", "D") == [3 * UN_DIA]


def test_un_feriado_no_es_hueco(conexion):
    # El día 3 no operó nadie: no hay hueco para nadie
    cargar_calendario(conexion, ["GGAL", "YPFD", "PAMP"], [1, 2, 4, 5])
    assert detectar_huecos(conexion, "GGAL", "D") == []


def test_no_inventa_historia_fuera_del_rango_del_ticker(conexion):
    # El mercado operó los días 1-6; GGAL listó el día 2 y su último dato es el 5
    cargar_calendario(conexion, ["YPFD", "PAMP"], [1, 2, 3, 4, 5, 6])
    guardar_velas(conexion, [vela("GGAL", d * UN_DIA) for d in (2, 3, 4, 5)])
    assert detectar_huecos(conexion, "GGAL", "D") == []


def test_los_mercados_no_se_mezclan(conexion):
    # BYMA operó el día 3; AAPL (otro calendario) no tiene por qué tenerlo
    cargar_calendario(conexion, ["GGAL", "YPFD"], [1, 2, 3])
    guardar_velas(conexion, [vela("AAPL", d * UN_DIA) for d in (1, 2)])
    assert detectar_huecos(conexion, "AAPL", "D") == []


def test_ticker_sin_velas_no_tiene_huecos(conexion):
    cargar_calendario(conexion, ["YPFD"], [1, 2, 3])
    assert detectar_huecos(conexion, "GGAL", "D") == []


def test_una_vela_faltante_no_suma_al_calendario(conexion):
    # El placeholder de YPFD del día 3 no convierte al día 3 en calendario real
    cargar_calendario(conexion, ["YPFD"], [1, 2])
    guardar_velas(
        conexion,
        [vela("YPFD", 3 * UN_DIA, apertura=0.0, maximo=0.0, minimo=0.0, cierre=0.0, es_faltante=1)],
    )
    guardar_velas(conexion, [vela("GGAL", d * UN_DIA) for d in (1, 2, 4)])
    cargar_calendario(conexion, ["PAMP"], [1, 2, 4])
    assert 3 * UN_DIA not in detectar_huecos(conexion, "GGAL", "D")


# --- placeholders ---


def test_crea_placeholders_con_flag_y_precios_en_cero(conexion):
    cargar_calendario(conexion, ["YPFD", "PAMP"], [1, 2, 3])
    guardar_velas(conexion, [vela("GGAL", d * UN_DIA) for d in (1, 3)])

    assert crear_placeholders(conexion, "GGAL", "D") == 1

    creada = [v for v in obtener_velas(conexion, "GGAL", "D") if v["ts"] == 2 * UN_DIA][0]
    assert creada["es_faltante"] == 1
    assert creada["cierre"] == 0.0
    assert creada["volumen"] == 0.0


def test_crear_placeholders_es_idempotente(conexion):
    cargar_calendario(conexion, ["YPFD", "PAMP"], [1, 2, 3])
    guardar_velas(conexion, [vela("GGAL", d * UN_DIA) for d in (1, 3)])
    assert crear_placeholders(conexion, "GGAL", "D") == 1
    assert crear_placeholders(conexion, "GGAL", "D") == 0


# --- redescarga dirigida ---


def faltante(ticker, ts):
    return vela(ticker, ts, apertura=0.0, maximo=0.0, minimo=0.0, cierre=0.0, volumen=0.0, es_faltante=1)


def test_redescarga_pide_el_rango_exacto_de_los_faltantes(conexion):
    guardar_velas(
        conexion,
        [vela("GGAL", 1 * UN_DIA), faltante("GGAL", 2 * UN_DIA), faltante("GGAL", 5 * UN_DIA), vela("GGAL", 6 * UN_DIA)],
    )
    with patch.object(reparador, "descargar_velas", return_value=[]) as descarga:
        redescargar_faltantes(conexion, "GGAL", "D")
    assert descarga.call_args.kwargs["desde"] == 2 * UN_DIA
    assert descarga.call_args.kwargs["hasta"] == 5 * UN_DIA + UN_DIA


def test_redescarga_limpia_el_flag_de_las_recuperadas(conexion):
    guardar_velas(conexion, [vela("GGAL", 1 * UN_DIA), faltante("GGAL", 2 * UN_DIA)])
    with patch.object(
        reparador, "descargar_velas", return_value=[vela("GGAL", 2 * UN_DIA, cierre=102.0)]
    ):
        assert redescargar_faltantes(conexion, "GGAL", "D") == 1
    reparada = [v for v in obtener_velas(conexion, "GGAL", "D") if v["ts"] == 2 * UN_DIA][0]
    assert reparada["es_faltante"] == 0
    assert reparada["cierre"] == 102.0


def test_redescarga_mantiene_el_flag_si_yfinance_no_lo_tiene(conexion):
    guardar_velas(conexion, [faltante("GGAL", 2 * UN_DIA), faltante("GGAL", 3 * UN_DIA)])
    with patch.object(
        reparador, "descargar_velas", return_value=[vela("GGAL", 2 * UN_DIA, cierre=102.0)]
    ):
        assert redescargar_faltantes(conexion, "GGAL", "D") == 1
    velas = {v["ts"]: v for v in obtener_velas(conexion, "GGAL", "D")}
    assert velas[2 * UN_DIA]["es_faltante"] == 0
    assert velas[3 * UN_DIA]["es_faltante"] == 1


def test_redescarga_sin_faltantes_no_llama_a_yfinance(conexion):
    guardar_velas(conexion, [vela("GGAL", UN_DIA)])
    with patch.object(reparador, "descargar_velas") as descarga:
        assert redescargar_faltantes(conexion, "GGAL", "D") == 0
    descarga.assert_not_called()


def test_redescarga_ignora_velas_que_no_estaban_faltantes(conexion):
    guardar_velas(conexion, [vela("GGAL", 1 * UN_DIA, cierre=100.0), faltante("GGAL", 2 * UN_DIA)])
    with patch.object(
        reparador,
        "descargar_velas",
        return_value=[vela("GGAL", 1 * UN_DIA, cierre=999.0), vela("GGAL", 2 * UN_DIA, cierre=102.0)],
    ):
        assert redescargar_faltantes(conexion, "GGAL", "D") == 1
    velas = {v["ts"]: v for v in obtener_velas(conexion, "GGAL", "D")}
    assert velas[1 * UN_DIA]["cierre"] == 100.0  # la vela sana no se pisa acá


# --- interpolación ---


def test_interpola_con_los_pesos_de_los_vecinos(conexion):
    guardar_velas(
        conexion,
        [
            vela("GGAL", 1 * UN_DIA, cierre=90.0, apertura=90.0, maximo=90.0, minimo=90.0),
            vela("GGAL", 2 * UN_DIA, cierre=100.0, apertura=100.0, maximo=100.0, minimo=100.0),
            faltante("GGAL", 3 * UN_DIA),
            vela("GGAL", 4 * UN_DIA, cierre=110.0, apertura=110.0, maximo=110.0, minimo=110.0),
            vela("GGAL", 5 * UN_DIA, cierre=120.0, apertura=120.0, maximo=120.0, minimo=120.0),
        ],
    )
    assert interpolar_faltantes(conexion, "GGAL", "D") == 1
    interpolada = [v for v in obtener_velas(conexion, "GGAL", "D") if v["ts"] == 3 * UN_DIA][0]
    # 0.1*90 + 0.4*100 + 0.4*110 + 0.1*120 = 105
    assert interpolada["cierre"] == 105.0
    assert interpolada["apertura"] == 105.0


def test_interpolada_conserva_el_flag_y_volumen_cero(conexion):
    guardar_velas(conexion, [vela("GGAL", 1 * UN_DIA), faltante("GGAL", 2 * UN_DIA), vela("GGAL", 3 * UN_DIA)])
    interpolar_faltantes(conexion, "GGAL", "D")
    interpolada = [v for v in obtener_velas(conexion, "GGAL", "D") if v["ts"] == 2 * UN_DIA][0]
    assert interpolada["es_faltante"] == 1
    assert interpolada["volumen"] == 0.0
    assert interpolada["cierre"] > 0


def test_interpola_en_el_borde_renormalizando(conexion):
    guardar_velas(
        conexion,
        [
            faltante("GGAL", 1 * UN_DIA),
            vela("GGAL", 2 * UN_DIA, cierre=100.0, apertura=100.0, maximo=100.0, minimo=100.0),
            vela("GGAL", 3 * UN_DIA, cierre=110.0, apertura=110.0, maximo=110.0, minimo=110.0),
        ],
    )
    interpolar_faltantes(conexion, "GGAL", "D")
    borde = obtener_velas(conexion, "GGAL", "D")[0]
    # (0.4*100 + 0.1*110) / 0.5 = 102
    assert borde["cierre"] == 102.0


def test_faltantes_consecutivos_no_se_usan_entre_si(conexion):
    guardar_velas(
        conexion,
        [
            vela("GGAL", 1 * UN_DIA, cierre=100.0, apertura=100.0, maximo=100.0, minimo=100.0),
            faltante("GGAL", 2 * UN_DIA),
            faltante("GGAL", 3 * UN_DIA),
            vela("GGAL", 4 * UN_DIA, cierre=110.0, apertura=110.0, maximo=110.0, minimo=110.0),
        ],
    )
    assert interpolar_faltantes(conexion, "GGAL", "D") == 2
    velas = obtener_velas(conexion, "GGAL", "D")
    assert velas[1]["cierre"] == 102.0  # (0.4*100 + 0.1*110) / 0.5
    assert velas[2]["cierre"] == 108.0  # (0.1*100 + 0.4*110) / 0.5


def test_sin_vecinas_reales_no_interpola(conexion):
    guardar_velas(conexion, [faltante("GGAL", 1 * UN_DIA), faltante("GGAL", 2 * UN_DIA)])
    assert interpolar_faltantes(conexion, "GGAL", "D") == 0
    assert all(v["cierre"] == 0.0 for v in obtener_velas(conexion, "GGAL", "D"))


# --- endpoints y enganche al sync ---


def test_endpoint_faltantes_resume_por_ticker(cliente, conexion):
    guardar_velas(
        conexion,
        [vela("GGAL", UN_DIA), faltante("GGAL", 2 * UN_DIA), faltante("YPFD", UN_DIA)],
    )
    datos = cliente.get("/api/faltantes").json()
    assert datos["total"] == 2
    assert {"ticker": "GGAL", "temporalidad": "D", "faltantes": 1} in datos["detalle"]


def test_endpoint_reparar_corre_el_pipeline(cliente, conexion):
    cargar_calendario(conexion, ["YPFD", "PAMP"], [1, 2, 3])
    guardar_velas(conexion, [vela("GGAL", d * UN_DIA) for d in (1, 3)])

    with patch.object(reparador, "descargar_velas", return_value=[]):
        resumen = cliente.post("/api/reparar").json()

    assert resumen["placeholders_creados"] == 1
    assert resumen["interpoladas"] == 1
    assert cliente.get("/api/faltantes").json()["total"] == 1  # interpolada: flag intacto


def test_el_sync_en_background_engancha_la_reparacion(conexion):
    import time

    import app.servicios.dolar as dolar
    import app.servicios.sincronizador as sincronizador

    resumen_sync = {"velas_guardadas": 0, "pares_sincronizados": 0, "velas_refrescadas": 0, "errores": []}
    with patch.object(sincronizador, "sincronizar_todo", return_value=dict(resumen_sync)), \
         patch.object(sincronizador, "obtener_conexion", return_value=conexion), \
         patch.object(reparador, "descargar_velas", return_value=[]), \
         patch.object(dolar, "descargar_velas", return_value=[]):  # nunca tocar la red
        assert sincronizador.sincronizar_en_background()
        limite = time.time() + 2
        while sincronizador.hay_sync_en_curso() and time.time() < limite:
            time.sleep(0.01)

    resumen = sincronizador.ultimo_resumen()
    assert "reparacion" in resumen
    assert "ccl" in resumen
    assert "dolar_oficial" in resumen
