"""Señales del día: unicidad por barra, evaluación tras el sync y endpoints."""
from app.repositorios import bots as repo_bots
from app.repositorios import senales as repo
from app.repositorios.velas import guardar_velas
from app.servicios.bots.senales import (
    anotar_vigencia,
    evaluar_senales,
    ids_vencidas,
)


# --- repositorio ---


def test_guardar_es_idempotente_por_barra(conexion):
    detalle = {"bot": "X"}
    assert repo.guardar(conexion, 1, "GGAL", 100, "entrada", detalle) is True
    # Misma barra y lado: no se duplica
    assert repo.guardar(conexion, 1, "GGAL", 100, "entrada", detalle) is False
    assert len(repo.listar(conexion)) == 1


def test_contar_y_marcar_sin_ver(conexion):
    repo.guardar(conexion, 1, "GGAL", 100, "entrada", {})
    repo.guardar(conexion, 1, "GGAL", 200, "entrada", {})
    assert repo.contar_sin_ver(conexion) == 2
    assert repo.marcar_todas_vistas(conexion) == 2
    assert repo.contar_sin_ver(conexion) == 0


def test_listar_ordena_mas_nueva_primero(conexion):
    repo.guardar(conexion, 1, "GGAL", 100, "entrada", {})
    repo.guardar(conexion, 1, "GGAL", 300, "entrada", {})
    repo.guardar(conexion, 1, "GGAL", 200, "entrada", {})
    assert [s["ts_barra"] for s in repo.listar(conexion)] == [300, 200, 100]


# --- evaluación tras el sync ---


def _sembrar_velas(conexion, cierres, ticker="GGAL"):
    guardar_velas(
        conexion,
        [
            {
                "ticker": ticker,
                "temporalidad": "D",
                "ts": (i + 1) * 86400,
                "apertura": c,
                "maximo": c + 1,
                "minimo": c - 1,
                "cierre": c,
                "volumen": 1000,
                "es_faltante": 0,
            }
            for i, c in enumerate(cierres)
        ],
    )


# Un bot que dispara cuando la EMA(1) — el cierre — supera 20
REGLAS_MAYOR_20 = {
    "version": 1,
    "entrada": [
        {"indicador": "ema", "serie": "ema", "operador": "mayor", "objetivo": 20, "params": {"periodo": 1}}
    ],
    "salida": [],
    "filtros": [],
}


def test_dispara_una_vez_y_no_re_dispara_en_el_proximo_sync(conexion):
    _sembrar_velas(conexion, [10, 15, 30])  # la última barra (30) cumple
    repo_bots.crear(conexion, "Bot GGAL", "GGAL", "D", "ARS", reglas=REGLAS_MAYOR_20)

    assert evaluar_senales(conexion) == 1  # nace la señal
    assert evaluar_senales(conexion) == 0  # mismo dato: no re-dispara
    senales = repo.listar(conexion)
    assert len(senales) == 1
    assert senales[0]["ticker"] == "GGAL"
    assert senales[0]["lado"] == "entrada"
    assert senales[0]["detalle"]["bot"] == "Bot GGAL"


def test_la_senal_guarda_el_desglose_de_condiciones(conexion):
    _sembrar_velas(conexion, [10, 15, 30])
    repo_bots.crear(conexion, "Bot GGAL", "GGAL", "D", "ARS", reglas=REGLAS_MAYOR_20)
    evaluar_senales(conexion)

    condiciones = repo.listar(conexion)[0]["detalle"]["condiciones"]
    assert len(condiciones) == 1
    cond = condiciones[0]
    assert cond["indicador"] == "ema" and cond["operador"] == "mayor"
    assert cond["objetivo"] == 20
    assert cond["valor"] == 30  # el cierre de la última barra
    assert cond["cumple"] is True


def test_vigencia_cambia_al_llegar_una_barra_que_no_cumple(conexion):
    _sembrar_velas(conexion, [10, 15, 30])
    repo_bots.crear(conexion, "Bot GGAL", "GGAL", "D", "ARS", reglas=REGLAS_MAYOR_20)
    evaluar_senales(conexion)

    # Mientras la última barra sigue cumpliendo, la señal está vigente
    vigentes = anotar_vigencia(conexion, repo.listar(conexion))
    assert vigentes[0]["vigente"] is True
    assert ids_vencidas(conexion, repo.listar(conexion)) == []

    # Llega una barra nueva que NO cumple (cierre 5): la señal vieja ya no vigente
    guardar_velas(
        conexion,
        [{"ticker": "GGAL", "temporalidad": "D", "ts": 4 * 86400, "apertura": 5,
          "maximo": 6, "minimo": 4, "cierre": 5, "volumen": 1, "es_faltante": 0}],
    )
    senales = repo.listar(conexion)
    assert anotar_vigencia(conexion, senales)[0]["vigente"] is False
    assert ids_vencidas(conexion, repo.listar(conexion)) == [senales[0]["id"]]


def test_no_dispara_si_la_ultima_barra_no_cumple(conexion):
    _sembrar_velas(conexion, [30, 25, 10])  # la última (10) no supera 20
    repo_bots.crear(conexion, "Bot GGAL", "GGAL", "D", "ARS", reglas=REGLAS_MAYOR_20)
    assert evaluar_senales(conexion) == 0


def test_los_bots_pausados_no_generan_senales(conexion):
    _sembrar_velas(conexion, [10, 15, 30])
    repo_bots.crear(conexion, "Bot GGAL", "GGAL", "D", "ARS", reglas=REGLAS_MAYOR_20, activo=False)
    assert evaluar_senales(conexion) == 0


def test_una_barra_nueva_que_cumple_dispara_de_nuevo(conexion):
    _sembrar_velas(conexion, [10, 15, 30])
    repo_bots.crear(conexion, "Bot GGAL", "GGAL", "D", "ARS", reglas=REGLAS_MAYOR_20)
    assert evaluar_senales(conexion) == 1
    # Llega otra barra que también cumple: es otra ts_barra → nueva señal
    guardar_velas(
        conexion,
        [{"ticker": "GGAL", "temporalidad": "D", "ts": 4 * 86400, "apertura": 31,
          "maximo": 32, "minimo": 30, "cierre": 31, "volumen": 1, "es_faltante": 0}],
    )
    assert evaluar_senales(conexion) == 1
    assert len(repo.listar(conexion)) == 2


# --- endpoints ---


def test_endpoint_lista_y_marca_vistas(cliente, conexion):
    repo.guardar(conexion, 1, "GGAL", 100, "entrada", {"bot": "X"})
    respuesta = cliente.get("/api/senales").json()
    assert respuesta["sin_ver"] == 1
    assert respuesta["senales"][0]["ticker"] == "GGAL"

    assert cliente.post("/api/senales/vistas").json() == {"marcadas": 1}
    assert cliente.get("/api/senales").json()["sin_ver"] == 0


def test_eliminar_una_senal(cliente, conexion):
    repo.guardar(conexion, 1, "GGAL", 100, "entrada", {})
    id_senal = repo.listar(conexion)[0]["id"]
    assert cliente.delete(f"/api/senales/{id_senal}").status_code == 200
    assert cliente.delete(f"/api/senales/{id_senal}").status_code == 404
    assert cliente.get("/api/senales").json()["senales"] == []


def test_eliminar_vencidas_solo_borra_las_que_no_se_cumplen(cliente, conexion):
    # Bot GGAL: su última barra cumple → su señal queda vigente
    _sembrar_velas(conexion, [10, 15, 30], ticker="GGAL")
    repo_bots.crear(conexion, "Bot GGAL", "GGAL", "D", "ARS", reglas=REGLAS_MAYOR_20)
    # Bot AAPL: dispara y después llega una barra que rompe la entrada
    _sembrar_velas(conexion, [10, 15, 30], ticker="AAPL")
    repo_bots.crear(conexion, "Bot AAPL", "AAPL", "D", "ARS", reglas=REGLAS_MAYOR_20)
    evaluar_senales(conexion)
    guardar_velas(
        conexion,
        [{"ticker": "AAPL", "temporalidad": "D", "ts": 4 * 86400, "apertura": 5,
          "maximo": 6, "minimo": 4, "cierre": 5, "volumen": 1, "es_faltante": 0}],
    )

    respuesta = cliente.post("/api/senales/eliminar_vencidas").json()
    assert respuesta["eliminadas"] == 1  # solo la de AAPL (ya no se cumple)
    quedan = cliente.get("/api/senales").json()["senales"]
    assert [s["ticker"] for s in quedan] == ["GGAL"]


def test_endpoint_anota_vigencia(cliente, conexion):
    _sembrar_velas(conexion, [10, 15, 30])
    repo_bots.crear(conexion, "Bot GGAL", "GGAL", "D", "ARS", reglas=REGLAS_MAYOR_20)
    evaluar_senales(conexion)
    senal = cliente.get("/api/senales").json()["senales"][0]
    assert senal["vigente"] is True


def test_borrar_bot_borra_sus_senales(cliente, conexion):
    _sembrar_velas(conexion, [10, 15, 30])
    bot = cliente.post(
        "/api/bots",
        json={"nombre": "Bot GGAL", "ticker": "GGAL", "temporalidad": "D", "reglas": REGLAS_MAYOR_20},
    ).json()
    evaluar_senales(conexion)
    assert cliente.get("/api/senales").json()["sin_ver"] == 1

    cliente.delete(f"/api/bots/{bot['id']}")
    assert cliente.get("/api/senales").json()["senales"] == []
