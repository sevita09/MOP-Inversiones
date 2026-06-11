import random

from app.repositorios.velas import guardar_velas, obtener_velas

UN_DIA = 86400


def generar_velas(ticker="GGAL", temporalidad="D", cantidad=30, semilla=42):
    azar = random.Random(semilla)
    velas = []
    precio = 100.0
    for i in range(cantidad):
        apertura = precio
        cierre = round(apertura * (1 + azar.uniform(-0.05, 0.05)), 2)
        maximo = round(max(apertura, cierre) * (1 + azar.uniform(0, 0.02)), 2)
        minimo = round(min(apertura, cierre) * (1 - azar.uniform(0, 0.02)), 2)
        velas.append(
            {
                "ticker": ticker,
                "temporalidad": temporalidad,
                "ts": (i + 1) * UN_DIA,
                "apertura": apertura,
                "maximo": maximo,
                "minimo": minimo,
                "cierre": cierre,
                "volumen": azar.randint(1000, 50000),
            }
        )
        precio = cierre
    return velas


def test_guardar_y_obtener_devuelve_todas(conexion):
    velas = generar_velas(cantidad=30)
    assert guardar_velas(conexion, velas) == 30
    assert len(obtener_velas(conexion, "GGAL", "D")) == 30


def test_obtener_ordena_por_ts(conexion):
    velas = generar_velas(cantidad=10)
    random.Random(7).shuffle(velas)
    guardar_velas(conexion, velas)
    resultado = obtener_velas(conexion, "GGAL", "D")
    tiempos = [vela["ts"] for vela in resultado]
    assert tiempos == sorted(tiempos)


def test_guardar_dos_veces_no_duplica(conexion):
    velas = generar_velas(cantidad=10)
    guardar_velas(conexion, velas)
    guardar_velas(conexion, velas)
    assert len(obtener_velas(conexion, "GGAL", "D")) == 10


def test_guardar_reemplaza_la_vela_existente(conexion):
    vela = generar_velas(cantidad=1)[0]
    guardar_velas(conexion, [vela])
    vela_corregida = dict(vela, cierre=999.0)
    guardar_velas(conexion, [vela_corregida])
    resultado = obtener_velas(conexion, "GGAL", "D")
    assert len(resultado) == 1
    assert resultado[0]["cierre"] == 999.0


def test_filtro_desde_hasta(conexion):
    guardar_velas(conexion, generar_velas(cantidad=10))
    resultado = obtener_velas(
        conexion, "GGAL", "D", desde=3 * UN_DIA, hasta=6 * UN_DIA
    )
    assert [vela["ts"] for vela in resultado] == [
        3 * UN_DIA,
        4 * UN_DIA,
        5 * UN_DIA,
        6 * UN_DIA,
    ]


def test_no_mezcla_tickers_ni_temporalidades(conexion):
    guardar_velas(conexion, generar_velas(ticker="GGAL", temporalidad="D"))
    guardar_velas(conexion, generar_velas(ticker="GGAL", temporalidad="S"))
    guardar_velas(conexion, generar_velas(ticker="YPFD", temporalidad="D"))
    assert len(obtener_velas(conexion, "GGAL", "D")) == 30
    assert all(v["temporalidad"] == "D" for v in obtener_velas(conexion, "GGAL", "D"))
    assert all(v["ticker"] == "YPFD" for v in obtener_velas(conexion, "YPFD", "D"))


def test_volumen_y_faltante_tienen_default(conexion):
    vela = generar_velas(cantidad=1)[0]
    del vela["volumen"]
    guardar_velas(conexion, [vela])
    resultado = obtener_velas(conexion, "GGAL", "D")[0]
    assert resultado["volumen"] == 0.0
    assert resultado["es_faltante"] == 0
