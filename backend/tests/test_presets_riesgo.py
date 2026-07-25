PRESET = {
    "nombre": "Conservador",
    "riesgo": {"stop_loss_pct": 8, "trailing_pct": 15, "salida_ema_central": True},
}


def test_crear_listar_y_eliminar_preset(cliente):
    creado = cliente.post("/api/riesgo/presets", json=PRESET)
    assert creado.status_code == 201
    cuerpo = creado.json()
    assert cuerpo["nombre"] == "Conservador"
    assert cuerpo["riesgo"]["stop_loss_pct"] == 8
    assert cuerpo["riesgo"]["salida_ema_central"] is True
    # el riesgo se completa con los defaults del esquema
    assert cuerpo["riesgo"]["atr_periodo"] == 14

    assert [p["nombre"] for p in cliente.get("/api/riesgo/presets").json()] == ["Conservador"]

    assert cliente.delete(f"/api/riesgo/presets/{cuerpo['id']}").status_code == 200
    assert cliente.get("/api/riesgo/presets").json() == []


def test_nombre_duplicado_es_409(cliente):
    cliente.post("/api/riesgo/presets", json=PRESET)
    assert cliente.post("/api/riesgo/presets", json=PRESET).status_code == 409


def test_riesgo_invalido_es_422(cliente):
    malo = {"nombre": "X", "riesgo": {"stop_loss_pct": 200}}
    assert cliente.post("/api/riesgo/presets", json=malo).status_code == 422


def test_eliminar_inexistente_es_404(cliente):
    assert cliente.delete("/api/riesgo/presets/999").status_code == 404
