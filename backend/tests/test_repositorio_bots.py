from app.repositorios import bots as repo


def _crear_bot(conexion, nombre="Reversión GGAL", **extra):
    datos = {"ticker": "GGAL", "temporalidad": "D", "moneda": "USD"}
    datos.update(extra)
    return repo.crear(conexion, nombre, **datos)


def test_crear_devuelve_el_bot_completo(conexion):
    bot = _crear_bot(conexion)
    assert bot["id"] == 1
    assert bot["nombre"] == "Reversión GGAL"
    assert bot["ticker"] == "GGAL"
    assert bot["temporalidad"] == "D"
    assert bot["moneda"] == "USD"
    assert bot["activo"] is True
    assert bot["capital"] == repo.CAPITAL_DEFAULT
    assert bot["reglas"] == repo.REGLAS_DEFAULT
    assert bot["creado"] and bot["actualizado"]


def test_nombre_duplicado_devuelve_none(conexion):
    _crear_bot(conexion)
    assert _crear_bot(conexion) is None


def test_listar_ordena_por_nombre(conexion):
    _crear_bot(conexion, nombre="Zeta")
    _crear_bot(conexion, nombre="Alfa")
    assert [b["nombre"] for b in repo.listar(conexion)] == ["Alfa", "Zeta"]


def test_obtener_inexistente_devuelve_none(conexion):
    assert repo.obtener(conexion, 99) is None


def test_actualizar_campos_sueltos(conexion):
    bot = _crear_bot(conexion)
    cambiado = repo.actualizar(
        conexion, bot["id"], {"nombre": "Otro", "activo": False, "capital": {"inicial": 5}}
    )
    assert cambiado["nombre"] == "Otro"
    assert cambiado["activo"] is False
    assert cambiado["capital"] == {"inicial": 5}
    # Lo no tocado queda igual
    assert cambiado["ticker"] == "GGAL"


def test_actualizar_a_nombre_que_choca_devuelve_none(conexion):
    _crear_bot(conexion, nombre="Uno")
    bot = _crear_bot(conexion, nombre="Dos")
    assert repo.actualizar(conexion, bot["id"], {"nombre": "Uno"}) is None


def test_actualizar_inexistente_devuelve_false(conexion):
    assert repo.actualizar(conexion, 99, {"nombre": "X"}) is False


def test_eliminar(conexion):
    bot = _crear_bot(conexion)
    assert repo.eliminar(conexion, bot["id"]) is True
    assert repo.eliminar(conexion, bot["id"]) is False
    assert repo.listar(conexion) == []


def test_duplicar_copia_con_sufijo(conexion):
    bot = _crear_bot(conexion, reglas={"version": 1, "entrada": [{"x": 1}], "salida": [], "filtros": []})
    copia = repo.duplicar(conexion, bot["id"])
    assert copia["nombre"] == "Reversión GGAL (copia)"
    assert copia["ticker"] == bot["ticker"]
    assert copia["reglas"] == bot["reglas"]
    assert copia["id"] != bot["id"]


def test_duplicar_dos_veces_numera_las_copias(conexion):
    bot = _crear_bot(conexion)
    repo.duplicar(conexion, bot["id"])
    segunda = repo.duplicar(conexion, bot["id"])
    assert segunda["nombre"] == "Reversión GGAL (copia 2)"


def test_duplicar_inexistente_devuelve_none(conexion):
    assert repo.duplicar(conexion, 99) is None
