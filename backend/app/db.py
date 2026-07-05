from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Union

from app.rutas import dir_datos

# En desarrollo: raíz del repo (gitignoreada). Empaquetada: ~/Library/Application Support/MOP
RUTA_BASE_DE_DATOS = dir_datos() / "mop.db"

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

CREATE TABLE IF NOT EXISTS dibujos (
    id       INTEGER PRIMARY KEY AUTOINCREMENT,
    ticker   TEXT NOT NULL,
    tipo     TEXT NOT NULL,   -- "horizontal", "tendencia", "fibonacci", "medicion"
    datos    TEXT NOT NULL,   -- JSON con puntos y propiedades
    creado   TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_dibujos_ticker ON dibujos(ticker);
"""

RutaBase = Union[Path, str]


def obtener_conexion(ruta: RutaBase = RUTA_BASE_DE_DATOS) -> sqlite3.Connection:
    # check_same_thread=False: FastAPI corre los endpoints sync en un pool de
    # threads, así que la conexión (una por request) puede crearse y usarse en
    # threads distintos. No se comparten conexiones entre requests, así que es seguro.
    conexion = sqlite3.connect(ruta, check_same_thread=False)
    conexion.row_factory = sqlite3.Row
    # Esperar a un lock de escritura (el sync en background) en vez de fallar al toque
    conexion.execute("PRAGMA busy_timeout = 5000")
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
