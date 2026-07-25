import pytest

BOT = {
    "nombre": "Reversión GGAL",
    "ticker": "GGAL",
    "temporalidad": "D",
    "moneda": "USD",
}


@pytest.fixture
def bot(cliente):
    return cliente.post("/api/bots", json=BOT).json()


# --- alta ---


def test_crear_bot_con_defaults(cliente):
    respuesta = cliente.post("/api/bots", json=BOT)
    assert respuesta.status_code == 201
    creado = respuesta.json()
    assert creado["nombre"] == "Reversión GGAL"
    assert creado["capital"] == {"inicial": 1000000, "porcentaje_por_posicion": 100}
    assert creado["reglas"] == {"version": 1, "entrada": [], "salida": [], "filtros": []}
    assert creado["activo"] is True


def test_ticker_se_normaliza_a_mayusculas(cliente):
    creado = cliente.post("/api/bots", json={**BOT, "ticker": "ggal"}).json()
    assert creado["ticker"] == "GGAL"


def test_nombre_duplicado_da_409(cliente, bot):
    assert cliente.post("/api/bots", json={**BOT, "ticker": "BMA"}).status_code == 409


def test_nombre_vacio_es_invalido(cliente):
    assert cliente.post("/api/bots", json={**BOT, "nombre": "  "}).status_code == 422


def test_ticker_desconocido_es_invalido(cliente):
    assert cliente.post("/api/bots", json={**BOT, "ticker": "NADA"}).status_code == 422


def test_tickers_de_dolar_quedan_afuera(cliente):
    assert cliente.post("/api/bots", json={**BOT, "ticker": "DOLARCCL"}).status_code == 422


def test_temporalidad_horaria_es_invalida(cliente):
    assert cliente.post("/api/bots", json={**BOT, "temporalidad": "H"}).status_code == 422


def test_capital_invalido_es_422(cliente):
    peticion = {**BOT, "capital": {"inicial": -5, "porcentaje_por_posicion": 100}}
    assert cliente.post("/api/bots", json=peticion).status_code == 422


REGLA_Z = {"indicador": "bandas", "serie": "z", "operador": "menor", "objetivo": -2}


def test_crear_bot_con_reglas(cliente):
    peticion = {**BOT, "reglas": {"version": 1, "entrada": [REGLA_Z], "salida": [], "filtros": []}}
    creado = cliente.post("/api/bots", json=peticion).json()
    assert creado["reglas"]["entrada"] == [REGLA_Z]


def test_crear_bot_con_reglas_invalidas_es_422(cliente):
    regla_rota = {**REGLA_Z, "indicador": "magia"}
    peticion = {**BOT, "reglas": {"version": 1, "entrada": [regla_rota], "salida": [], "filtros": []}}
    assert cliente.post("/api/bots", json=peticion).status_code == 422


def test_editar_las_reglas_de_un_bot(cliente, bot):
    reglas = {"version": 1, "entrada": [REGLA_Z], "salida": [], "filtros": []}
    editado = cliente.put(f"/api/bots/{bot['id']}", json={"reglas": reglas}).json()
    assert editado["reglas"]["entrada"] == [REGLA_Z]
    assert editado["nombre"] == bot["nombre"]


def test_riesgo_por_defecto_y_edicion(cliente, bot):
    # Un bot nuevo trae la config de riesgo vacía (sin stops)
    assert bot["riesgo"]["stop_loss_pct"] is None
    assert bot["riesgo"]["salida_ema_central"] is False
    # Se puede editar
    editado = cliente.put(
        f"/api/bots/{bot['id']}",
        json={"riesgo": {"stop_loss_pct": 8, "take_profit_pct": 20, "salida_ema_central": True}},
    ).json()
    assert editado["riesgo"]["stop_loss_pct"] == 8
    assert editado["riesgo"]["take_profit_pct"] == 20
    assert editado["riesgo"]["salida_ema_central"] is True


def test_riesgo_invalido_es_422(cliente):
    peticion = {**BOT, "riesgo": {"stop_loss_pct": 150}}  # > 100
    assert cliente.post("/api/bots", json=peticion).status_code == 422


# --- lectura ---


def test_listar_y_obtener(cliente, bot):
    assert cliente.get("/api/bots").json() == [bot]
    assert cliente.get(f"/api/bots/{bot['id']}").json() == bot


def test_obtener_inexistente_es_404(cliente):
    assert cliente.get("/api/bots/99").status_code == 404


# --- edición ---


def test_editar_campos_sueltos(cliente, bot):
    respuesta = cliente.put(
        f"/api/bots/{bot['id']}", json={"nombre": "Otro", "activo": False}
    )
    assert respuesta.status_code == 200
    editado = respuesta.json()
    assert editado["nombre"] == "Otro"
    assert editado["activo"] is False
    assert editado["ticker"] == "GGAL"


def test_editar_a_nombre_ocupado_da_409(cliente, bot):
    cliente.post("/api/bots", json={**BOT, "nombre": "Otro"})
    respuesta = cliente.put(f"/api/bots/{bot['id']}", json={"nombre": "Otro"})
    assert respuesta.status_code == 409


def test_editar_inexistente_es_404(cliente):
    assert cliente.put("/api/bots/99", json={"nombre": "X"}).status_code == 404


# --- borrado y duplicado ---


def test_eliminar_bot(cliente, bot):
    assert cliente.delete(f"/api/bots/{bot['id']}").status_code == 200
    assert cliente.get("/api/bots").json() == []
    assert cliente.delete(f"/api/bots/{bot['id']}").status_code == 404


def test_duplicar_bot(cliente, bot):
    respuesta = cliente.post(f"/api/bots/{bot['id']}/duplicar")
    assert respuesta.status_code == 201
    assert respuesta.json()["nombre"] == "Reversión GGAL (copia)"
    assert len(cliente.get("/api/bots").json()) == 2


def test_duplicar_inexistente_es_404(cliente):
    assert cliente.post("/api/bots/99/duplicar").status_code == 404
