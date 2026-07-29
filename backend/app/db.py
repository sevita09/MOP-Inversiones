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

CREATE TABLE IF NOT EXISTS categorias (
    id     INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS categorias_tickers (
    categoria_id INTEGER NOT NULL,
    ticker       TEXT NOT NULL,
    PRIMARY KEY (categoria_id, ticker)
);

CREATE TABLE IF NOT EXISTS favoritos (
    ticker TEXT PRIMARY KEY
);

CREATE TABLE IF NOT EXISTS tickers_extra (
    ticker     TEXT PRIMARY KEY,   -- como se muestra en la app
    simbolo_yf TEXT NOT NULL,      -- símbolo resuelto en Yahoo Finance
    grupo      TEXT NOT NULL DEFAULT 'cedears',  -- panel del sidebar al que pertenece
    agregado   TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS bots (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre       TEXT NOT NULL UNIQUE,
    ticker       TEXT NOT NULL,
    temporalidad TEXT NOT NULL,   -- D, S o M (la horaria queda fuera de los bots)
    moneda       TEXT NOT NULL DEFAULT 'ARS',
    capital_json TEXT NOT NULL,   -- {"inicial": ..., "porcentaje_por_posicion": ...}
    reglas_json  TEXT NOT NULL,   -- {"version": 1, "entrada": [...], "salida": [...], "filtros": [...]}
    riesgo_json  TEXT,            -- gestión de riesgo (stop, take profit, trailing, sizing); NULL = sin riesgo
    activo       INTEGER NOT NULL DEFAULT 1,
    metricas_json TEXT,           -- resumen del último backtest (caché); NULL si nunca corrió
    creado       TEXT NOT NULL DEFAULT (datetime('now')),
    actualizado  TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Plantillas de estrategia propias del usuario (las 4 de la metodología viven
-- fijas en servicios/bots/plantillas.py; estas son las que él guarda y persisten)
CREATE TABLE IF NOT EXISTS plantillas (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre       TEXT NOT NULL UNIQUE,
    descripcion  TEXT NOT NULL DEFAULT '',
    temporalidad TEXT NOT NULL,
    moneda       TEXT NOT NULL DEFAULT 'USD',
    reglas_json  TEXT NOT NULL,
    creado       TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Señales que dispara un bot activo sobre su última barra tras cada sync.
-- Única por (bot_id, ts_barra, lado): el sync corre seguido y no debe duplicar.
CREATE TABLE IF NOT EXISTS senales (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    bot_id       INTEGER NOT NULL,
    ticker       TEXT NOT NULL,
    ts_barra     INTEGER NOT NULL,
    lado         TEXT NOT NULL,     -- 'entrada' (la salida llega con la cartera)
    detalle_json TEXT NOT NULL DEFAULT '{}',
    vista        INTEGER NOT NULL DEFAULT 0,
    creado       TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE (bot_id, ts_barra, lado)
);

-- Splits (y splits inversos) de un papel. No mueven plata: multiplican la
-- cantidad de papeles y dividen su precio, dejando el costo total igual.
-- `ratio` = papeles nuevos por cada papel viejo (3 = split 3:1; 0.1 = inverso 1:10).
CREATE TABLE IF NOT EXISTS splits (
    id     INTEGER PRIMARY KEY AUTOINCREMENT,
    ticker TEXT NOT NULL,
    fecha  TEXT NOT NULL,   -- AAAA-MM-DD, desde cuándo rige
    ratio  REAL NOT NULL,
    nota   TEXT NOT NULL DEFAULT '',
    creado TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE (ticker, fecha)
);

-- Preferencias del usuario (clave/valor). Hoy: tasas de comisión de la cartera.
CREATE TABLE IF NOT EXISTS configuracion (
    clave TEXT PRIMARY KEY,
    valor TEXT NOT NULL
);

-- Operaciones reales del usuario. El precio va SIEMPRE en ARS (es como se opera
-- en BYMA); la vista en USD se calcula con la tasa CCL de la fecha.
CREATE TABLE IF NOT EXISTS transacciones (
    id       INTEGER PRIMARY KEY AUTOINCREMENT,
    ticker   TEXT NOT NULL,
    tipo     TEXT NOT NULL,              -- 'compra' | 'venta'
    fecha    TEXT NOT NULL,              -- AAAA-MM-DD
    cantidad REAL NOT NULL,
    precio   REAL NOT NULL,              -- ARS por unidad
    comision REAL NOT NULL DEFAULT 0,    -- ARS totales de la operación
    nota     TEXT NOT NULL DEFAULT '',
    creado   TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_transacciones_ticker ON transacciones(ticker, fecha);

-- Configuraciones de riesgo guardadas por el usuario, para reusar entre bots
CREATE TABLE IF NOT EXISTS presets_riesgo (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre      TEXT NOT NULL UNIQUE,
    riesgo_json TEXT NOT NULL,
    creado      TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Inflación mensual (IPC nacional del INDEC, vía api.argentinadatos.com).
-- `valor` es la variación porcentual de ese mes, no un índice.
CREATE TABLE IF NOT EXISTS inflacion (
    fecha  TEXT PRIMARY KEY,   -- AAAA-MM-DD, último día del mes medido
    valor  REAL NOT NULL       -- variación % del mes
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
        # Migración suave: bases creadas antes de que tickers_extra tuviera grupo
        try:
            conexion.execute(
                "ALTER TABLE tickers_extra ADD COLUMN grupo TEXT NOT NULL DEFAULT 'cedears'"
            )
        except sqlite3.OperationalError:
            pass  # la columna ya existe
        # Migración suave: bases creadas antes del caché de métricas del backtest
        try:
            conexion.execute("ALTER TABLE bots ADD COLUMN metricas_json TEXT")
        except sqlite3.OperationalError:
            pass  # la columna ya existe
        # Migración suave: bases creadas antes de la gestión de riesgo
        try:
            conexion.execute("ALTER TABLE bots ADD COLUMN riesgo_json TEXT")
        except sqlite3.OperationalError:
            pass  # la columna ya existe


def conexion_api():
    """Dependencia de FastAPI: una conexión por request, cerrada al terminar."""
    conexion = obtener_conexion()
    try:
        yield conexion
    finally:
        conexion.close()
