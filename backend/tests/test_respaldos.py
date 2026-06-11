from datetime import date

from app.servicios.respaldos import respaldar_base, rotar_respaldos


def crear_base(carpeta, contenido=b"datos"):
    base = carpeta / "mop.db"
    base.write_bytes(contenido)
    return base


def test_respalda_la_base_con_fecha_del_dia(tmp_path):
    base = crear_base(tmp_path, b"contenido original")
    respaldo = respaldar_base(base)
    assert respaldo is not None
    assert respaldo.name == f"mop-{date.today().isoformat()}.db"
    assert respaldo.read_bytes() == b"contenido original"


def test_no_respalda_si_no_hay_base(tmp_path):
    assert respaldar_base(tmp_path / "mop.db") is None
    assert not (tmp_path / "backups").exists()


def test_no_duplica_respaldo_del_mismo_dia(tmp_path):
    base = crear_base(tmp_path)
    primero = respaldar_base(base)
    segundo = respaldar_base(base)
    assert primero is not None
    assert segundo is None
    assert len(list((tmp_path / "backups").glob("mop-*.db"))) == 1


def test_rotacion_conserva_los_ultimos_siete(tmp_path):
    for dia in range(1, 11):
        (tmp_path / f"mop-2026-01-{dia:02d}.db").write_bytes(b"x")

    borrados = rotar_respaldos(tmp_path, conservar=7)

    restantes = sorted(ruta.name for ruta in tmp_path.glob("mop-*.db"))
    assert borrados == 3
    assert len(restantes) == 7
    # Quedan los siete más nuevos: del 04 al 10
    assert restantes[0] == "mop-2026-01-04.db"
    assert restantes[-1] == "mop-2026-01-10.db"


def test_rotacion_no_borra_si_hay_menos_que_el_limite(tmp_path):
    for dia in range(1, 4):
        (tmp_path / f"mop-2026-01-{dia:02d}.db").write_bytes(b"x")

    assert rotar_respaldos(tmp_path, conservar=7) == 0
    assert len(list(tmp_path.glob("mop-*.db"))) == 3


def test_respaldar_dispara_la_rotacion(tmp_path):
    base = crear_base(tmp_path)
    carpeta = tmp_path / "backups"
    carpeta.mkdir()
    for dia in range(1, 8):
        (carpeta / f"mop-2025-12-{dia:02d}.db").write_bytes(b"x")

    respaldar_base(base, carpeta_respaldos=carpeta, conservar=7)

    restantes = sorted(ruta.name for ruta in carpeta.glob("mop-*.db"))
    assert len(restantes) == 7
    assert "mop-2025-12-01.db" not in restantes
    assert f"mop-{date.today().isoformat()}.db" in restantes
