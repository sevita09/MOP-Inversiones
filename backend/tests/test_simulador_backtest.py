"""Simulador de backtest: ejecución en la apertura siguiente, sin lookahead,
y Buy & Hold con las mismas entradas."""
from app.servicios.backtest.simulador import correr_backtest, simular


def _barras(precios):
    """Barras diarias; cada precio es (apertura, cierre). Máx/mín amplios."""
    barras = []
    for i, (ap, ci) in enumerate(precios):
        barras.append(
            {
                "ts": (i + 1) * 86400,
                "apertura": ap,
                "maximo": max(ap, ci) + 1,
                "minimo": min(ap, ci) - 1,
                "cierre": ci,
                "volumen": 1000,
            }
        )
    return barras


def test_ejecuta_en_la_apertura_de_la_barra_siguiente():
    # Señal de entrada en la barra 1 (ts 86400) → entra en la apertura de la 2
    barras = _barras([(10, 10), (12, 14), (16, 18), (20, 20)])
    ts = [b["ts"] for b in barras]
    resultado = simular(barras, ts_entrada={ts[0]}, ts_salida={ts[2]}, capital_inicial=1000, fraccion=1.0)

    trade = resultado["trades"][0]
    assert trade["entrada_ts"] == ts[1]  # barra siguiente a la señal
    assert trade["entrada_precio"] == 12  # la APERTURA de esa barra
    assert trade["salida_ts"] == ts[3]  # señal de salida en ts[2] → sale en ts[3]
    assert trade["salida_precio"] == 20
    # 1000 → compra a 12, vende a 20: factor 20/12
    assert resultado["capital_final"] == round(1000 * 20 / 12, 2)


def test_no_lookahead_la_senal_no_se_ejecuta_en_su_misma_barra():
    # Entrada Y salida señaladas en la misma barra 0: no puede operar en la barra 0
    barras = _barras([(10, 10), (12, 12)])
    ts = [b["ts"] for b in barras]
    resultado = simular(barras, ts_entrada={ts[0]}, ts_salida=set(), capital_inicial=1000, fraccion=1.0)
    # Entra recién en la apertura de la barra 1 (12), no en la 0
    assert resultado["trades"][0]["entrada_ts"] == ts[1]


def test_posicion_abierta_al_final_se_cierra_al_cierre():
    barras = _barras([(10, 10), (12, 14), (16, 18)])
    ts = [b["ts"] for b in barras]
    resultado = simular(barras, ts_entrada={ts[0]}, ts_salida=set(), capital_inicial=1000, fraccion=1.0)
    trade = resultado["trades"][0]
    assert trade["abierto_al_final"] is True
    assert trade["salida_precio"] == 18  # cierre de la última barra
    assert trade["salida_ts"] == ts[2]


def test_fraccion_parcial_compromete_solo_parte_del_capital():
    barras = _barras([(10, 10), (10, 10), (20, 20)])
    ts = [b["ts"] for b in barras]
    # 50% del capital: la mitad opera (dobla), la mitad queda en efectivo
    resultado = simular(barras, ts_entrada={ts[0]}, ts_salida={ts[1]}, capital_inicial=1000, fraccion=0.5)
    # entra a 10 con 500 (50 unidades), sale a 20 → 1000; +500 en caja = 1500
    assert resultado["capital_final"] == 1500.0


def test_gana_y_pierde_se_marcan_bien():
    barras = _barras([(10, 10), (10, 10), (8, 8)])
    ts = [b["ts"] for b in barras]
    resultado = simular(barras, ts_entrada={ts[0]}, ts_salida={ts[1]}, capital_inicial=1000, fraccion=1.0)
    trade = resultado["trades"][0]
    assert trade["gana"] is False
    assert trade["pnl_pct"] == -20.0


# --- correr_backtest: estrategia vs buy & hold ---


def _bot(reglas):
    return {
        "ticker": "GGAL",
        "temporalidad": "D",
        "moneda": "ARS",
        "capital": {"inicial": 1000, "porcentaje_por_posicion": 100},
        "reglas": reglas,
    }


def test_buy_and_hold_usa_las_mismas_entradas_sin_salir(conexion):
    from app.repositorios.velas import guardar_velas

    # Precio que sube y baja: ema(1) > 15 dispara entradas; la salida corta antes de la caída
    precios = [10, 12, 20, 25, 18, 12, 30]
    guardar_velas(
        conexion,
        [
            {"ticker": "GGAL", "temporalidad": "D", "ts": (i + 1) * 86400, "apertura": p,
             "maximo": p + 1, "minimo": p - 1, "cierre": p, "volumen": 1000, "es_faltante": 0}
            for i, p in enumerate(precios)
        ],
    )
    reglas = {
        "version": 1,
        "entrada": [{"indicador": "ema", "serie": "ema", "operador": "mayor", "objetivo": 15, "params": {"periodo": 1}}],
        "salida": [{"indicador": "ema", "serie": "ema", "operador": "menor", "objetivo": 15, "params": {"periodo": 1}}],
        "filtros": [],
    }
    resultado = correr_backtest(conexion, _bot(reglas))

    assert resultado["estrategia"]["trades"], "la estrategia tiene que operar"
    assert resultado["buy_and_hold"]["trades"], "el buy & hold entra en la misma señal"
    # B&H entra en la misma primera entrada que la estrategia
    assert (
        resultado["buy_and_hold"]["trades"][0]["entrada_ts"]
        == resultado["estrategia"]["trades"][0]["entrada_ts"]
    )
    # B&H nunca cierra por regla: su único trade queda abierto al final
    assert len(resultado["buy_and_hold"]["trades"]) == 1
    assert resultado["buy_and_hold"]["trades"][0]["abierto_al_final"] is True


def test_backtest_sin_datos_no_rompe(conexion):
    reglas = {
        "version": 1,
        "entrada": [{"indicador": "ema", "serie": "ema", "operador": "mayor", "objetivo": 1, "params": {"periodo": 1}}],
        "salida": [], "filtros": [],
    }
    resultado = correr_backtest(conexion, _bot(reglas))
    assert resultado["estrategia"]["trades"] == []
    assert resultado["desde"] is None
