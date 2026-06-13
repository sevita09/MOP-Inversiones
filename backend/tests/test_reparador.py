from app.repositorios.velas import guardar_velas, obtener_velas
from app.servicios.reparador import (
    crear_placeholders,
    detectar_huecos,
    marcar_corruptas,
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
