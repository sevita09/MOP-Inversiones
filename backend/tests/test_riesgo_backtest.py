"""Gestión de riesgo del simulador: stops (contra high/low, prioridad al stop),
take profit, trailing y sizing por volatilidad."""
from app.servicios.backtest.riesgo import (
    niveles_iniciales,
    salida_intrabarra,
    unidades_a_comprar,
)
from app.servicios.backtest.simulador import simular


def _barra(ts, ap, mx, mn, ci):
    return {"ts": ts, "apertura": ap, "maximo": mx, "minimo": mn, "cierre": ci, "volumen": 1000}


def _serie(precios):
    """Barras diarias desde (apertura, maximo, minimo, cierre)."""
    return [_barra((i + 1) * 86400, *p) for i, p in enumerate(precios)]


# --- niveles y salida intra-barra ---


def test_stop_fijo_y_atr_toma_el_mas_protector():
    # entrada 100: stop 10% = 90; stop 2 ATR con ATR 3 = 94 → gana el más alto (94)
    stop, tp = niveles_iniciales(100, {"stop_loss_pct": 10, "stop_atr_mult": 2}, atr_entrada=3)
    assert stop == 94
    assert tp is None


def test_stop_tiene_prioridad_sobre_take_profit():
    # Una barra que toca AMBOS: low 88 (stop 90) y high 112 (tp 110). Conservador: stop
    barra = _barra(0, 100, 112, 88, 100)
    precio, motivo = salida_intrabarra(barra, stop=90, tp=110)
    assert motivo == "stop"
    assert precio == 90


def test_gap_por_debajo_del_stop_se_llena_en_la_apertura():
    # Abrió en 85, por debajo del stop 90 → se ejecuta a 85, no a 90
    barra = _barra(0, 85, 88, 84, 86)
    precio, motivo = salida_intrabarra(barra, stop=90, tp=None)
    assert motivo == "stop" and precio == 85


def test_take_profit_cuando_no_toca_el_stop():
    barra = _barra(0, 100, 115, 98, 112)
    precio, motivo = salida_intrabarra(barra, stop=90, tp=110)
    assert motivo == "take_profit" and precio == 110


# --- simulación completa con riesgo ---


def test_stop_loss_corta_la_perdida():
    # Entra en la barra 2 (apertura 100). La barra 3 cae a low 88 → stop 90 salta
    barras = _serie([(10, 11, 9, 10), (100, 101, 99, 100), (95, 96, 88, 90), (80, 81, 79, 80)])
    ts = [b["ts"] for b in barras]
    resultado = simular(
        barras, {ts[0]}, set(), 1000, 1.0, riesgo={"stop_loss_pct": 10}
    )
    trade = resultado["trades"][0]
    assert trade["motivo"] == "stop"
    assert trade["salida_precio"] == 90  # el stop, no el cierre 80
    assert trade["pnl_pct"] == -10.0


def test_take_profit_toma_la_ganancia():
    barras = _serie([(10, 11, 9, 10), (100, 101, 99, 100), (105, 130, 104, 120)])
    ts = [b["ts"] for b in barras]
    resultado = simular(
        barras, {ts[0]}, set(), 1000, 1.0, riesgo={"take_profit_pct": 20}
    )
    trade = resultado["trades"][0]
    assert trade["motivo"] == "take_profit"
    assert trade["salida_precio"] == 120  # entrada 100 + 20%


def test_trailing_stop_sube_con_el_maximo():
    # Entra a 100; sube a 150 (trailing 10% = 135); luego cae y toca 135
    barras = _serie([
        (10, 11, 9, 10),
        (100, 120, 99, 118),   # entra a 100, máximo 120 → trailing 108
        (119, 150, 118, 148),  # máximo 150 → trailing 135
        (140, 141, 130, 134),  # low 130 < 135 → sale a 135
    ])
    ts = [b["ts"] for b in barras]
    resultado = simular(
        barras, {ts[0]}, set(), 1000, 1.0, riesgo={"trailing_pct": 10}
    )
    trade = resultado["trades"][0]
    assert trade["motivo"] == "stop"
    assert trade["salida_precio"] == 135


# --- sizing por riesgo/volatilidad ---


def test_sizing_por_riesgo_ajusta_las_unidades_al_stop():
    # Capital 1000, arriesgo 2% (=20) hasta un stop a 90 desde 100: pierdo 10/u
    # → 20/10 = 2 unidades
    unidades = unidades_a_comprar(1000, 1.0, entrada=100, stop=90, riesgo={"sizing_riesgo_pct": 2})
    assert unidades == 2.0


def test_sizing_por_riesgo_no_apalanca():
    # Stop muy cerca (99): 2% / 1 = 20 unidades = 2000 > 1000 → se topa en 10 unidades
    unidades = unidades_a_comprar(1000, 1.0, entrada=100, stop=99, riesgo={"sizing_riesgo_pct": 2})
    assert unidades == 10.0  # 1000 / 100


def test_sin_stop_el_sizing_por_riesgo_cae_a_la_fraccion():
    unidades = unidades_a_comprar(1000, 0.5, entrada=100, stop=None, riesgo={"sizing_riesgo_pct": 2})
    assert unidades == 5.0  # 500 / 100


# --- salida por EMA central (vía backtest real) ---


def test_salida_por_ema_central_corta_al_cruzar(conexion):
    from app.repositorios.velas import guardar_velas
    from app.servicios.backtest.simulador import correr_backtest

    # En D la EMA central es de 200 barras: 210 barras planas a 100 la dejan en ~100,
    # y una caída sostenida a 50 la cruza hacia abajo con barras de sobra por delante
    precios = [100] * 210 + [50] * 30
    guardar_velas(
        conexion,
        [
            {"ticker": "GGAL", "temporalidad": "D", "ts": (i + 1) * 86400, "apertura": p,
             "maximo": p + 0.5, "minimo": p - 0.5, "cierre": p, "volumen": 1000, "es_faltante": 0}
            for i, p in enumerate(precios)
        ],
    )
    entrada = {"indicador": "ema", "serie": "ema", "operador": "mayor", "objetivo": 60, "params": {"periodo": 1}}
    base = {
        "ticker": "GGAL", "temporalidad": "D", "moneda": "ARS",
        "capital": {"inicial": 1000, "porcentaje_por_posicion": 100},
        "reglas": {"version": 1, "entrada": [entrada], "salida": [], "filtros": []},
    }
    con_ema = correr_backtest(conexion, {**base, "riesgo": {"salida_ema_central": True}})
    sin_ema = correr_backtest(conexion, {**base, "riesgo": {}})

    # Con la salida en la EMA, el trade cierra por la señal del cruce (no al final)
    assert con_ema["estrategia"]["trades"][0]["abierto_al_final"] is False
    # Sin ella, la posición queda abierta hasta el final del rango
    assert sin_ema["estrategia"]["trades"][0]["abierto_al_final"] is True
