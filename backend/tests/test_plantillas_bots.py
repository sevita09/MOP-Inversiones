from app.esquemas.reglas import Reglas
from app.servicios.bots.plantillas import PLANTILLAS


def test_hay_cuatro_plantillas_con_sus_claves():
    claves = [p["clave"] for p in PLANTILLAS]
    assert claves == [
        "triple_confluencia",
        "reversion_semanal",
        "sobreextension_percentil",
        "cruce_de_emas",
    ]


def test_cada_plantilla_produce_reglas_validas():
    for plantilla in PLANTILLAS:
        reglas = Reglas(**plantilla["reglas"])
        assert reglas.version == 1
        assert len(reglas.entrada) > 0, plantilla["clave"]


def test_cada_plantilla_ejecuta_en_diario_y_en_dolares():
    # Decisión de la metodología: el z es limpio en USD (serie ADR) y el
    # diario es el TF de ejecución; la señal nace en S/M vía confluencia
    for plantilla in PLANTILLAS:
        assert plantilla["temporalidad"] == "D", plantilla["clave"]
        assert plantilla["moneda"] == "USD", plantilla["clave"]
        assert plantilla["descripcion"] and plantilla["horizonte"]


def test_la_triple_confluencia_es_la_de_la_metodologia():
    triple = PLANTILLAS[0]["reglas"]
    temporalidades = [c.get("temporalidad") for c in triple["entrada"]]
    assert temporalidades == ["M", "S", None]  # None = la del bot (D)
    assert triple["salida"][0]["temporalidad"] == "S"


def test_endpoint_de_plantillas(cliente):
    respuesta = cliente.get("/api/plantillas")
    assert respuesta.status_code == 200
    predefinidas = respuesta.json()
    assert [p["clave"] for p in predefinidas] == [p["clave"] for p in PLANTILLAS]
    assert all(p["predefinida"] for p in predefinidas)
    assert all(p["id"] is None for p in predefinidas)


# --- plantillas propias del usuario ---

PLANTILLA_PROPIA = {
    "nombre": "Mi reversión diaria",
    "descripcion": "Prueba propia",
    "temporalidad": "D",
    "moneda": "USD",
    "reglas": {
        "version": 1,
        "entrada": [{"indicador": "rsi", "serie": "rsi", "operador": "menor", "objetivo": 30}],
        "salida": [],
        "filtros": [],
    },
}


def test_crear_plantilla_propia_aparece_en_el_listado(cliente):
    creada = cliente.post("/api/plantillas", json=PLANTILLA_PROPIA)
    assert creada.status_code == 201
    cuerpo = creada.json()
    assert cuerpo["predefinida"] is False
    assert cuerpo["id"] is not None
    assert cuerpo["clave"] == f"custom:{cuerpo['id']}"

    listado = cliente.get("/api/plantillas").json()
    # Las 4 de la metodología + la propia, al final
    assert len(listado) == len(PLANTILLAS) + 1
    assert listado[-1]["nombre"] == "Mi reversión diaria"


def test_plantilla_propia_con_reglas_invalidas_es_422(cliente):
    rota = {**PLANTILLA_PROPIA, "reglas": {
        "version": 1,
        "entrada": [{"indicador": "magia", "serie": "x", "operador": "mayor", "objetivo": 1}],
        "salida": [], "filtros": [],
    }}
    assert cliente.post("/api/plantillas", json=rota).status_code == 422


def test_nombre_de_plantilla_duplicado_es_409(cliente):
    cliente.post("/api/plantillas", json=PLANTILLA_PROPIA)
    assert cliente.post("/api/plantillas", json=PLANTILLA_PROPIA).status_code == 409


def test_no_se_puede_pisar_una_plantilla_de_la_metodologia(cliente):
    choca = {**PLANTILLA_PROPIA, "nombre": PLANTILLAS[0]["nombre"]}
    assert cliente.post("/api/plantillas", json=choca).status_code == 409


def test_eliminar_plantilla_propia(cliente):
    id_plantilla = cliente.post("/api/plantillas", json=PLANTILLA_PROPIA).json()["id"]
    assert cliente.delete(f"/api/plantillas/{id_plantilla}").status_code == 200
    assert cliente.delete(f"/api/plantillas/{id_plantilla}").status_code == 404
    assert len(cliente.get("/api/plantillas").json()) == len(PLANTILLAS)
