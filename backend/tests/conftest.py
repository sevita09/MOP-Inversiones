import sqlite3

import pytest

from app.db import ESQUEMA


@pytest.fixture
def conexion():
    """Base SQLite en memoria con el esquema completo, una por test."""
    con = sqlite3.connect(":memory:")
    con.row_factory = sqlite3.Row
    con.executescript(ESQUEMA)
    yield con
    con.close()
