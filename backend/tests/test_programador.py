from datetime import datetime, timezone

from app.servicios.programador import (
    INTERVALO_FUERA,
    INTERVALO_RUEDA,
    ZONA_ARGENTINA,
    en_rueda,
    proximo_intervalo,
)
from app.servicios.sincronizador import (
    VIGENCIA_POR_TEMPORALIDAD,
    esta_vencido,
    vigencia_actual,
)


def hora_ar(dia: int, hora: int) -> datetime:
    """Un instante de junio 2026 en hora argentina (12=viernes, 13=sábado)."""
    return datetime(2026, 6, dia, hora, 30, tzinfo=ZONA_ARGENTINA)


# --- horario de rueda ---


def test_dia_habil_de_9_a_18_es_rueda():
    assert en_rueda(hora_ar(12, 9))
    assert en_rueda(hora_ar(12, 17))


def test_fuera_de_hora_no_es_rueda():
    assert not en_rueda(hora_ar(12, 8))
    assert not en_rueda(hora_ar(12, 18))
    assert not en_rueda(hora_ar(12, 23))


def test_finde_no_es_rueda():
    assert not en_rueda(hora_ar(13, 12))  # sábado
    assert not en_rueda(hora_ar(14, 12))  # domingo


def test_acepta_instantes_en_utc():
    # 12:00 UTC = 09:00 AR → rueda; 23:00 UTC = 20:00 AR → fuera
    assert en_rueda(datetime(2026, 6, 12, 12, 30, tzinfo=timezone.utc))
    assert not en_rueda(datetime(2026, 6, 12, 23, 0, tzinfo=timezone.utc))


def test_intervalo_segun_horario():
    assert proximo_intervalo(hora_ar(12, 11)) == INTERVALO_RUEDA
    assert proximo_intervalo(hora_ar(13, 11)) == INTERVALO_FUERA


# --- vigencias dinámicas ---


def test_en_rueda_h_y_d_envejecen_a_los_quince_minutos():
    momento = hora_ar(12, 11)
    assert vigencia_actual("H", momento) == INTERVALO_RUEDA
    assert vigencia_actual("D", momento) == INTERVALO_RUEDA
    # S y M mantienen sus vigencias largas incluso en rueda
    assert vigencia_actual("S", momento) == VIGENCIA_POR_TEMPORALIDAD["S"]
    assert vigencia_actual("M", momento) == VIGENCIA_POR_TEMPORALIDAD["M"]


def test_fuera_de_rueda_rigen_las_vigencias_normales():
    momento = hora_ar(13, 11)  # sábado
    assert vigencia_actual("D", momento) == VIGENCIA_POR_TEMPORALIDAD["D"]
    assert vigencia_actual("H", momento) == VIGENCIA_POR_TEMPORALIDAD["H"]


def test_vencimiento_intradiario_en_rueda():
    momento = hora_ar(12, 11)
    hace_20_min = datetime(2026, 6, 12, 11, 10, tzinfo=ZONA_ARGENTINA).isoformat()
    hace_5_min = datetime(2026, 6, 12, 11, 25, tzinfo=ZONA_ARGENTINA).isoformat()
    assert esta_vencido(hace_20_min, "D", momento)
    assert not esta_vencido(hace_5_min, "D", momento)
