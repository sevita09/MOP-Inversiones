from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Union

# La base vive en la raíz del repo (gitignoreada)
RUTA_BASE_DE_DATOS = Path(__file__).resolve().parents[2] / "mop.db"

ESQUEMA = """
CREATE TABLE IF NOT EXISTS velas (
    ticker       TEXT NOT NULL,
    temporalidad TEXT NOT NULL,
    ts           INTEGER NOT NULL,
    apertura     REAL NOT NULL,
    maximo       REAL NOT NULL,
    minimo       REAL NOT NULL,
    cierre       REAL NOT NULL,
    volumen      REAL NOT NULL DEFAULT 0,
    es_faltante  INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (ticker, temporalidad, ts)
);

CREATE TABLE IF NOT EXISTS registro_sync (
    ticker       TEXT NOT NULL,
    temporalidad TEXT NOT NULL,
    ultima_sync  TEXT NOT NULL,
    PRIMARY KEY (ticker, temporalidad)
);

CREATE TABLE IF NOT EXISTS tasas_dolar (
    fecha    TEXT NOT NULL,   -- AAAA-MM-DD
    tipo     TEXT NOT NULL,   -- "CCL" u "OFICIAL"
    valor    REAL NOT NULL,   -- ARS por USD
    PRIMARY KEY (fecha, tipo)
);
"""

RutaBase = Union[Path, str]


def obtener_conexion(ruta: RutaBase = RUTA_BASE_DE_DATOS) -> sqlite3.Connection:
    conexion = sqlite3.connect(ruta)
    conexion.row_factory = sqlite3.Row
    return conexion


def inicializar_base(ruta: RutaBase = RUTA_BASE_DE_DATOS) -> None:
    with obtener_conexion(ruta) as conexion:
        conexion.executescript(ESQUEMA)


def conexion_api():
    """Dependencia de FastAPI: una conexión por request, cerrada al terminar."""
    conexion = obtener_conexion()
    try:
        yield conexion
    finally:
        conexion.close()
