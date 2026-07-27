"""Grid search, walk-forward y detección de sobreajuste sobre datos sintéticos."""
import math

import pytest

from app.repositorios.velas import guardar_velas
from app.servicios.backtest.optimizador import (
    aplicar_valor,
    corte_walk_forward,
    evaluar_sobreajuste,
    optimizar,
    valores_de,
)


# --- generación de la grilla y aplicación de valores ---


def test_valores_de_arma_el_rango_inclusive():
    assert valores_de({"desde": 5, "hasta": 20, "paso": 5}) == [5, 10, 15, 20]
    assert valores_de({"desde": -3, "hasta": -1, "paso": 0.5}) == [-3, -2.5, -2, -1.5, -1]


def test_rango_invalido_es_error():
    with pytest.raises(ValueError):
        valores_de({"desde": 10, "hasta": 1, "paso": 1})
    with pytest.raises(ValueError):
        valores_de({"desde": 1, "hasta": 10, "paso": 0})


def test_aplicar_valor_en_condicion_y_en_riesgo():
    bot = {
        "reglas": {"entrada": [{"indicador": "bandas", "serie": "z", "objetivo": -2}], "salida": [], "filtros": []},
        "riesgo": {},
    }
    aplicar_valor(bot, {"tipo": "condicion", "bloque": "entrada", "indice": 0, "campo": "objetivo"}, -1.5)
    assert bot["reglas"]["entrada"][0]["objetivo"] == -1.5

    aplicar_valor(bot, {"tipo": "condicion", "bloque": "entrada", "indice": 0, "campo": "params.periodo"}, 30)
    assert bot["reglas"]["entrada"][0]["params"] == {"periodo": 30}

    aplicar_valor(bot, {"tipo": "riesgo", "campo": "stop_loss_pct"}, 8)
    assert bot["riesgo"]["stop_loss_pct"] == 8


def test_corte_walk_forward_deja_el_setenta_por_ciento():
    velas = [{"ts": i} for i in range(100)]
    assert corte_walk_forward(velas) == 70
    assert corte_walk_forward([{"ts": 1}]) is None  # muy pocas barras


# --- optimización punta a punta ---


def _sembrar(conexion, precios):
    guardar_velas(
        conexion,
        [
            {"ticker": "GGAL", "temporalidad": "D", "ts": (i + 1) * 86400, "apertura": p,
             "maximo": p + 1, "minimo": p - 1, "cierre": p, "volumen": 1000, "es_faltante": 0}
            for i, p in enumerate(precios)
        ],
    )


def _bot(objetivo=15):
    return {
        "id": 1, "ticker": "GGAL", "temporalidad": "D", "moneda": "ARS",
        "capital": {"inicial": 1000, "porcentaje_por_posicion": 100},
        "riesgo": {},
        "reglas": {
            "version": 1,
            "entrada": [{"indicador": "ema", "serie": "ema", "operador": "mayor",
                         "objetivo": objetivo, "params": {"periodo": 1}}],
            "salida": [{"indicador": "ema", "serie": "ema", "operador": "menor",
                        "objetivo": objetivo, "params": {"periodo": 1}}],
            "filtros": [],
        },
    }


PARAM_UMBRAL = {
    "tipo": "condicion", "bloque": "entrada", "indice": 0, "campo": "objetivo",
    "desde": 10, "hasta": 20, "paso": 5,
}


def test_optimizar_prueba_toda_la_grilla(conexion):
    _sembrar(conexion, [10 + 10 * math.sin(i / 5) for i in range(200)])
    salida = optimizar(conexion, _bot(), [PARAM_UMBRAL])

    assert [r["valores"] for r in salida["resultados"]] == [[10], [15], [20]]
    assert salida["mejor"] is not None
    assert salida["mejor"]["valores"] in ([10], [15], [20])


def test_optimizar_reporta_progreso(conexion):
    _sembrar(conexion, [10 + 10 * math.sin(i / 5) for i in range(120)])
    llamadas = []
    optimizar(conexion, _bot(), [PARAM_UMBRAL], progreso=lambda h, t: llamadas.append((h, t)))
    assert llamadas == [(1, 3), (2, 3), (3, 3)]


def test_optimizar_dos_parametros_hace_el_producto(conexion):
    _sembrar(conexion, [10 + 10 * math.sin(i / 5) for i in range(120)])
    segundo = {"tipo": "riesgo", "campo": "stop_loss_pct", "desde": 5, "hasta": 10, "paso": 5}
    salida = optimizar(conexion, _bot(), [PARAM_UMBRAL, segundo])
    assert len(salida["resultados"]) == 6  # 3 umbrales × 2 stops


def test_optimizar_valida_fuera_de_muestra(conexion):
    _sembrar(conexion, [10 + 10 * math.sin(i / 5) for i in range(200)])
    salida = optimizar(conexion, _bot(), [PARAM_UMBRAL])
    assert salida["corte_walk_forward"] is not None
    assert salida["validacion"] is not None
    # La validación es OTRO tramo: no tiene por qué dar igual que la optimización
    assert "retorno_pct" in salida["validacion"]


def test_mas_de_dos_parametros_es_error(conexion):
    with pytest.raises(ValueError, match="uno o dos"):
        optimizar(conexion, _bot(), [PARAM_UMBRAL, PARAM_UMBRAL, PARAM_UMBRAL])


def test_grilla_gigante_es_error(conexion):
    enorme = {**PARAM_UMBRAL, "desde": 0, "hasta": 1000, "paso": 1}
    with pytest.raises(ValueError, match="demasiado"):
        optimizar(conexion, _bot(), [enorme])


def test_metrica_desconocida_es_error(conexion):
    with pytest.raises(ValueError, match="Métrica desconocida"):
        optimizar(conexion, _bot(), [PARAM_UMBRAL], metrica="magia")


# --- avisos de sobreajuste ---


def _resultado(metrica, retorno=None, trades=30):
    return {
        "valores": [1], "metrica": metrica,
        "retorno_pct": retorno if retorno is not None else metrica,
        "trades": trades, "drawdown_pct": -5, "buy_and_hold_pct": 0,
    }


def test_avisa_cuando_hay_pocas_operaciones():
    mejor = _resultado(50, trades=3)
    aviso = evaluar_sobreajuste([mejor], mejor, None)
    assert aviso["hay_sobreajuste"] is True
    assert any("operaciones" in a for a in aviso["avisos"])


def test_avisa_cuando_el_mejor_es_un_pico_aislado():
    # Uno brilla (100) y el resto anda por 10: zona no robusta
    resultados = [_resultado(100)] + [_resultado(10) for _ in range(5)]
    aviso = evaluar_sobreajuste(resultados, resultados[0], None)
    assert any("pico aislado" in a for a in aviso["avisos"])


def test_no_avisa_pico_cuando_la_zona_es_robusta():
    # Todos parecidos: la ventaja no depende de un valor puntual
    resultados = [_resultado(100), _resultado(95), _resultado(92), _resultado(90), _resultado(88)]
    aviso = evaluar_sobreajuste(resultados, resultados[0], None)
    assert not any("pico aislado" in a for a in aviso["avisos"])


def test_avisa_cuando_no_valida_fuera_de_muestra():
    mejor = _resultado(60)
    validacion = {"retorno_pct": -10, "trades": 12, "metrica": -10, "drawdown_pct": -20, "buy_and_hold_pct": 5}
    aviso = evaluar_sobreajuste([mejor], mejor, validacion)
    assert any("validación" in a for a in aviso["avisos"])


def test_sin_avisos_cuando_todo_cierra():
    resultados = [_resultado(100), _resultado(95), _resultado(90), _resultado(85), _resultado(80)]
    validacion = {"retorno_pct": 80, "trades": 20, "metrica": 80, "drawdown_pct": -8, "buy_and_hold_pct": 10}
    aviso = evaluar_sobreajuste(resultados, resultados[0], validacion)
    assert aviso["hay_sobreajuste"] is False
    assert aviso["avisos"] == []
