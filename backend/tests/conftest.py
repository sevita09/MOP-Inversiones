import sqlite3

import pytest
from fastapi.testclient import TestClient

from app.db import ESQUEMA, conexion_api
from app.main import app


@pytest.fixture
def conexion():
    """Base SQLite en memoria con el esquema completo, una por test."""
    # check_same_thread=False: el TestClient corre los endpoints en otro thread
    con = sqlite3.connect(":memory:", check_same_thread=False)
    con.row_factory = sqlite3.Row
    con.executescript(ESQUEMA)
    yield con
    con.close()


@pytest.fixture
def cliente(conexion):
    """TestClient con la base en memoria inyectada (sin lifespan ni sync real)."""
    app.dependency_overrides[conexion_api] = lambda: conexion
    yield TestClient(app)
    app.dependency_overrides.clear()
