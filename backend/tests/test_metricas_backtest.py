"""Métricas de backtest con trades de resultado conocido."""
from app.servicios.backtest.metricas import calcular_metricas


def _trade(pnl_pct, gana=None):
    return {
        "entrada_ts": 0, "entrada_precio": 10, "salida_ts": 86400, "salida_precio": 10,
        "pnl_pct": pnl_pct, "duracion_dias": 1, "gana": gana if gana is not None else pnl_pct > 0,
        "abierto_al_final": False,
    }


def _sim(trades, curva, barras=None, en_posicion=None):
    return {
        "retorno_pct": round((curva[-1]["capital"] / curva[0]["capital"] - 1) * 100, 4) if curva else 0,
        "trades": trades,
        "curva": curva,
        "barras": barras if barras is not None else len(curva),
        "barras_en_posicion": en_posicion if en_posicion is not None else 0,
    }


def _curva(valores):
    return [{"ts": (i + 1) * 86400, "capital": v} for i, v in enumerate(valores)]


def test_win_rate_y_conteo_de_trades():
    trades = [_trade(10), _trade(-5), _trade(20), _trade(-2)]
    m = calcular_metricas(_sim(trades, _curva([1000, 1050])), "D")
    assert m["trades_total"] == 4
    assert m["trades_ganados"] == 2
    assert m["win_rate_pct"] == 50.0


def test_profit_factor_y_expectancy():
    trades = [_trade(30), _trade(-10)]  # ganancia bruta 30, pérdida bruta 10
    m = calcular_metricas(_sim(trades, _curva([1000, 1200])), "D")
    assert m["profit_factor"] == 3.0
    assert m["expectancy_pct"] == 10.0  # (30 - 10) / 2


def test_profit_factor_sin_perdidas_es_none():
    trades = [_trade(10), _trade(5)]
    m = calcular_metricas(_sim(trades, _curva([1000, 1100])), "D")
    assert m["profit_factor"] is None  # no hay con qué dividir


def test_drawdown_maximo():
    # Sube a 1200, cae a 900 (peor caída -25% desde el pico 1200), se recupera
    m = calcular_metricas(_sim([], _curva([1000, 1200, 900, 1100])), "D")
    assert m["drawdown_maximo_pct"] == -25.0


def test_racha_maxima_de_perdidas():
    trades = [_trade(10), _trade(-1), _trade(-1), _trade(-1), _trade(5), _trade(-1)]
    m = calcular_metricas(_sim(trades, _curva([1000, 1000])), "D")
    assert m["racha_maxima_perdidas"] == 3


def test_exposicion():
    # 10 barras, 4 en posición
    m = calcular_metricas(_sim([], _curva([1000] * 10), barras=10, en_posicion=4), "D")
    assert m["exposicion_pct"] == 40.0


def test_sharpe_de_curva_plana_es_none():
    m = calcular_metricas(_sim([], _curva([1000, 1000, 1000])), "D")
    assert m["sharpe"] is None  # sin variación no hay ratio


def test_sharpe_positivo_con_retornos_al_alza():
    m = calcular_metricas(_sim([], _curva([1000, 1010, 1020, 1035, 1050])), "D")
    assert m["sharpe"] is not None and m["sharpe"] > 0


def test_sin_trades_no_rompe():
    m = calcular_metricas(_sim([], _curva([1000, 1000])), "D")
    assert m["trades_total"] == 0
    assert m["win_rate_pct"] is None
    assert m["expectancy_pct"] is None
    assert m["racha_maxima_perdidas"] == 0
