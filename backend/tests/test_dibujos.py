def test_listar_vacio(cliente):
    resp = cliente.get("/api/dibujos?ticker=GGAL")
    assert resp.status_code == 200
    assert resp.json() == []


def test_crear_y_listar(cliente):
    body = {"ticker": "GGAL", "tipo": "horizontal", "datos": {"precio": 1500}}
    resp = cliente.post("/api/dibujos", json=body)
    assert resp.status_code == 201
    creado = resp.json()
    assert creado["id"] is not None
    assert creado["tipo"] == "horizontal"
    assert creado["datos"]["precio"] == 1500

    lista = cliente.get("/api/dibujos?ticker=GGAL").json()
    assert len(lista) == 1
    assert lista[0]["id"] == creado["id"]


def test_crear_tipo_invalido(cliente):
    body = {"ticker": "GGAL", "tipo": "invalido", "datos": {}}
    resp = cliente.post("/api/dibujos", json=body)
    assert resp.status_code == 422


def test_actualizar(cliente):
    body = {"ticker": "GGAL", "tipo": "tendencia", "datos": {"p1": [100, 50], "p2": [200, 60]}}
    creado = cliente.post("/api/dibujos", json=body).json()
    nuevos_datos = {"p1": [100, 55], "p2": [200, 65]}
    resp = cliente.put(f"/api/dibujos/{creado['id']}", json={"datos": nuevos_datos})
    assert resp.status_code == 200
    lista = cliente.get("/api/dibujos?ticker=GGAL").json()
    assert lista[0]["datos"] == nuevos_datos


def test_actualizar_inexistente(cliente):
    resp = cliente.put("/api/dibujos/9999", json={"datos": {}})
    assert resp.status_code == 404


def test_eliminar(cliente):
    body = {"ticker": "GGAL", "tipo": "fibonacci", "datos": {"p1": [100, 50], "p2": [200, 60]}}
    creado = cliente.post("/api/dibujos", json=body).json()
    resp = cliente.delete(f"/api/dibujos/{creado['id']}")
    assert resp.status_code == 200
    assert cliente.get("/api/dibujos?ticker=GGAL").json() == []


def test_eliminar_inexistente(cliente):
    resp = cliente.delete("/api/dibujos/9999")
    assert resp.status_code == 404


def test_dibujos_aislados_por_ticker(cliente):
    cliente.post("/api/dibujos", json={"ticker": "GGAL", "tipo": "horizontal", "datos": {"precio": 1500}})
    cliente.post("/api/dibujos", json={"ticker": "YPF", "tipo": "horizontal", "datos": {"precio": 30000}})
    assert len(cliente.get("/api/dibujos?ticker=GGAL").json()) == 1
    assert len(cliente.get("/api/dibujos?ticker=YPF").json()) == 1
