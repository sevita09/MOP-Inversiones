import pytest


@pytest.fixture
def categoria(cliente):
    return cliente.post("/api/categorias", json={"nombre": "Bancos"}).json()


# --- crud de categorías ---


def test_crear_y_listar_categorias(cliente):
    respuesta = cliente.post("/api/categorias", json={"nombre": "Energía"})
    assert respuesta.status_code == 201
    assert respuesta.json()["nombre"] == "Energía"

    listado = cliente.get("/api/categorias").json()
    assert [c["nombre"] for c in listado] == ["Energía"]
    assert listado[0]["tickers"] == []


def test_nombre_duplicado_da_conflicto(cliente, categoria):
    assert cliente.post("/api/categorias", json={"nombre": "Bancos"}).status_code == 409


def test_nombre_vacio_es_invalido(cliente):
    assert cliente.post("/api/categorias", json={"nombre": "   "}).status_code == 422


def test_eliminar_categoria_borra_sus_tickers(cliente, categoria):
    id_cat = categoria["id"]
    cliente.post(f"/api/categorias/{id_cat}/tickers", json={"ticker": "GGAL"})
    assert cliente.delete(f"/api/categorias/{id_cat}").status_code == 200
    assert cliente.get("/api/categorias").json() == []
    # Recrear con el mismo nombre arranca vacía (no heredó tickers)
    nueva = cliente.post("/api/categorias", json={"nombre": "Bancos"}).json()
    assert nueva["tickers"] == []


def test_eliminar_inexistente_es_404(cliente):
    assert cliente.delete("/api/categorias/999").status_code == 404


# --- tickers dentro de una categoría ---


def test_agregar_y_quitar_ticker(cliente, categoria):
    id_cat = categoria["id"]
    assert (
        cliente.post(f"/api/categorias/{id_cat}/tickers", json={"ticker": "ggal"}).status_code
        == 201
    )
    assert cliente.get("/api/categorias").json()[0]["tickers"] == ["GGAL"]

    assert cliente.delete(f"/api/categorias/{id_cat}/tickers/GGAL").status_code == 200
    assert cliente.get("/api/categorias").json()[0]["tickers"] == []


def test_agregar_ticker_es_idempotente(cliente, categoria):
    id_cat = categoria["id"]
    cliente.post(f"/api/categorias/{id_cat}/tickers", json={"ticker": "BMA"})
    cliente.post(f"/api/categorias/{id_cat}/tickers", json={"ticker": "BMA"})
    assert cliente.get("/api/categorias").json()[0]["tickers"] == ["BMA"]


def test_ticker_desconocido_es_invalido(cliente, categoria):
    respuesta = cliente.post(
        f"/api/categorias/{categoria['id']}/tickers", json={"ticker": "NOEXISTE"}
    )
    assert respuesta.status_code == 422


def test_agregar_a_categoria_inexistente_es_404(cliente):
    assert (
        cliente.post("/api/categorias/999/tickers", json={"ticker": "GGAL"}).status_code == 404
    )


# --- favoritos en la base ---


def test_favoritos_arrancan_vacios(cliente):
    assert cliente.get("/api/favoritos").json() == {"tickers": []}


def test_guardar_y_leer_favoritos_conservando_el_orden(cliente):
    respuesta = cliente.put(
        "/api/favoritos", json={"tickers": ["YPFD", "GGAL", "DOLARCCL"]}
    )
    assert respuesta.status_code == 200
    # El orden se conserva (es el orden en que el usuario los marcó)
    assert cliente.get("/api/favoritos").json() == {"tickers": ["YPFD", "GGAL", "DOLARCCL"]}


def test_guardar_favoritos_filtra_desconocidos(cliente):
    cliente.put("/api/favoritos", json={"tickers": ["GGAL", "CUALQUIERA"]})
    assert cliente.get("/api/favoritos").json() == {"tickers": ["GGAL"]}


def test_guardar_favoritos_reemplaza_la_lista(cliente):
    cliente.put("/api/favoritos", json={"tickers": ["GGAL", "BMA"]})
    cliente.put("/api/favoritos", json={"tickers": ["ALUA"]})
    assert cliente.get("/api/favoritos").json() == {"tickers": ["ALUA"]}
