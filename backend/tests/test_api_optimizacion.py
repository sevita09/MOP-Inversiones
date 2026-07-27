"""Endpoints de optimización: lanzar en background y consultar el progreso."""
import math
import time

from app.repositorios.velas import guardar_velas

PARAM = {
    "tipo": "condicion", "bloque": "entrada", "indice": 0, "campo": "objetivo",
    "desde": 10, "hasta": 20, "paso": 5,
}

REGLAS = {
    "version": 1,
    "entrada": [{"indicador": "ema", "serie": "ema", "operador": "mayor",
                 "objetivo": 15, "params": {"periodo": 1}}],
    "salida": [{"indicador": "ema", "serie": "ema", "operador": "menor",
                "objetivo": 15, "params": {"periodo": 1}}],
    "filtros": [],
}


def _sembrar(conexion, barras=200):
    guardar_velas(
        conexion,
        [
            {"ticker": "GGAL", "temporalidad": "D", "ts": (i + 1) * 86400,
             "apertura": 10 + 10 * math.sin(i / 5), "maximo": 21, "minimo": -1,
             "cierre": 10 + 10 * math.sin(i / 5), "volumen": 1000, "es_faltante": 0}
            for i in range(barras)
        ],
    )


def _crear_bot(cliente):
    return cliente.post(
        "/api/bots",
        json={"nombre": "Opt", "ticker": "GGAL", "temporalidad": "D", "reglas": REGLAS},
    ).json()


def _esperar_fin(cliente, intentos=60):
    for _ in range(intentos):
        estado = cliente.get("/api/optimizacion").json()
        if not estado["en_curso"]:
            return estado
        time.sleep(0.1)
    raise AssertionError("la optimización no terminó a tiempo")


def test_optimizacion_completa_con_walk_forward(cliente, conexion):
    _sembrar(conexion)
    bot = _crear_bot(cliente)

    respuesta = cliente.post(f"/api/optimizacion/{bot['id']}", json={"parametros": [PARAM]})
    assert respuesta.status_code == 202

    estado = _esperar_fin(cliente)
    assert estado["error"] is None
    resultado = estado["resultado"]
    assert len(resultado["resultados"]) == 3
    assert resultado["mejor"] is not None
    # Walk-forward: hay corte y validación fuera de muestra
    assert resultado["corte_walk_forward"] is not None
    assert resultado["validacion"] is not None
    assert "sobreajuste" in resultado


def test_el_progreso_termina_completo(cliente, conexion):
    _sembrar(conexion)
    bot = _crear_bot(cliente)
    cliente.post(f"/api/optimizacion/{bot['id']}", json={"parametros": [PARAM]})
    estado = _esperar_fin(cliente)
    assert estado["hechos"] == estado["total"] == 3


def test_optimizar_bot_inexistente_es_404(cliente):
    assert cliente.post("/api/optimizacion/999", json={"parametros": [PARAM]}).status_code == 404


def test_optimizar_condicion_que_no_existe_es_422(cliente, conexion):
    _sembrar(conexion)
    bot = _crear_bot(cliente)
    fuera_de_rango = {**PARAM, "indice": 5}
    respuesta = cliente.post(
        f"/api/optimizacion/{bot['id']}", json={"parametros": [fuera_de_rango]}
    )
    assert respuesta.status_code == 422


def test_optimizar_sin_reglas_de_entrada_es_422(cliente, conexion):
    _sembrar(conexion)
    vacio = cliente.post(
        "/api/bots", json={"nombre": "Vacio", "ticker": "GGAL", "temporalidad": "D"}
    ).json()
    respuesta = cliente.post(f"/api/optimizacion/{vacio['id']}", json={"parametros": [PARAM]})
    assert respuesta.status_code == 422


def test_mas_de_dos_parametros_es_422(cliente, conexion):
    _sembrar(conexion)
    bot = _crear_bot(cliente)
    respuesta = cliente.post(
        f"/api/optimizacion/{bot['id']}", json={"parametros": [PARAM, PARAM, PARAM]}
    )
    assert respuesta.status_code == 422
