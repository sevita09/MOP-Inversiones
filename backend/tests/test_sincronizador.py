from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import app.servicios.sincronizador as sincronizador
from app.repositorios.registro_sync import obtener_ultima_sync, registrar_sync
from app.repositorios.velas import guardar_velas, obtener_ultima_vela, obtener_velas
from app.servicios.sincronizador import (
    esta_vencido,
    refrescar_velas_en_curso,
    sincronizar_ticker,
    sincronizar_todo,
)

AHORA = datetime(2026, 6, 12, 15, 0, tzinfo=timezone.utc)
UN_DIA = 86400
LUNES = int(datetime(2026, 6, 8, tzinfo=timezone.utc).timestamp())


def vela_diaria(ts, cierre=100.0, maximo=None, minimo=None, volumen=1000.0):
    return {
        "ticker": "GGAL",
        "temporalidad": "D",
        "ts": ts,
        "apertura": cierre,
        "maximo": maximo or cierre,
        "minimo": minimo or cierre,
        "cierre": cierre,
        "volumen": volumen,
    }


def hace(**kwargs):
    return (AHORA - timedelta(**kwargs)).isoformat()


def test_nunca_sincronizado_esta_vencido():
    assert esta_vencido(None, "D", AHORA)


def test_vigencia_por_temporalidad():
    assert not esta_vencido(hace(hours=2), "D", AHORA)
    assert esta_vencido(hace(days=2), "D", AHORA)
    assert esta_vencido(hace(hours=2), "H", AHORA)
    assert not esta_vencido(hace(days=2), "S", AHORA)
    assert esta_vencido(hace(days=8), "S", AHORA)
    assert not esta_vencido(hace(days=15), "M", AHORA)
    assert esta_vencido(hace(days=31), "M", AHORA)


def test_primera_sync_baja_historia_completa(conexion):
    with patch.object(
        sincronizador, "descargar_velas", return_value=[vela_diaria(LUNES)]
    ) as descarga:
        guardadas = sincronizar_ticker(conexion, "GGAL", "D", AHORA)
    assert guardadas == 1
    assert descarga.call_args.kwargs["desde"] is None
    assert obtener_ultima_sync(conexion, "GGAL", "D") == AHORA.isoformat()


def test_sync_delta_arranca_en_la_ultima_vela(conexion):
    guardar_velas(conexion, [vela_diaria(LUNES)])
    registrar_sync(conexion, "GGAL", "D", hace(days=2))
    with patch.object(sincronizador, "descargar_velas", return_value=[]) as descarga:
        sincronizar_ticker(conexion, "GGAL", "D", AHORA)
    assert descarga.call_args.kwargs["desde"] == LUNES


def test_sync_vigente_no_descarga(conexion):
    registrar_sync(conexion, "GGAL", "D", hace(hours=1))
    with patch.object(sincronizador, "descargar_velas") as descarga:
        assert sincronizar_ticker(conexion, "GGAL", "D", AHORA) == 0
    descarga.assert_not_called()


def test_refresco_completa_la_vela_semanal_en_curso(conexion):
    guardar_velas(
        conexion,
        [
            {
                "ticker": "GGAL",
                "temporalidad": "S",
                "ts": LUNES,
                "apertura": 100,
                "maximo": 105,
                "minimo": 99,
                "cierre": 104,
                "volumen": 1000,
            },
            vela_diaria(LUNES, cierre=104, maximo=105, minimo=99),
            vela_diaria(LUNES + UN_DIA, cierre=108, maximo=110, minimo=103, volumen=800),
            vela_diaria(LUNES + 2 * UN_DIA, cierre=112, maximo=114, minimo=107, volumen=900),
            # Lunes de la semana siguiente: NO debe entrar en la vela en curso
            vela_diaria(LUNES + 7 * UN_DIA, cierre=60, maximo=200, minimo=50, volumen=99),
        ],
    )
    registrar_sync(conexion, "GGAL", "S", hace(days=2))
    registrar_sync(conexion, "GGAL", "D", hace(hours=1))

    assert refrescar_velas_en_curso(conexion, "GGAL") == 1

    vela = obtener_ultima_vela(conexion, "GGAL", "S")
    assert vela["cierre"] == 112
    assert vela["maximo"] == 114
    assert vela["minimo"] == 99
    assert vela["volumen"] == 1000 + 800 + 900


def test_refresco_no_aplica_si_la_semanal_esta_mas_actualizada(conexion):
    guardar_velas(conexion, [vela_diaria(LUNES)])
    registrar_sync(conexion, "GGAL", "S", hace(hours=1))
    registrar_sync(conexion, "GGAL", "D", hace(days=1))
    assert refrescar_velas_en_curso(conexion, "GGAL") == 0


def test_sincronizar_todo_acumula_errores_sin_frenar(conexion):
    def descarga_con_fallo(ticker, temporalidad, desde=None):
        if ticker == "GGAL":
            raise RuntimeError("yfinance caído")
        return [dict(vela_diaria(LUNES), ticker=ticker)]

    with patch.object(sincronizador, "todos_los_tickers", return_value=["GGAL", "YPFD"]), \
         patch.object(sincronizador, "TEMPORALIDADES", ["D"]), \
         patch.object(sincronizador, "descargar_velas", descarga_con_fallo):
        resumen = sincronizar_todo(conexion, AHORA)

    assert resumen["velas_guardadas"] == 1
    assert len(resumen["errores"]) == 1
    assert "GGAL/D" in resumen["errores"][0]
    assert len(obtener_velas(conexion, "YPFD", "D")) == 1
