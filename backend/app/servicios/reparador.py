"""Reparación de velas faltantes o corruptas.

Pipeline (se completa a lo largo de la feature):
1. Marcar velas con precios en cero como faltantes.
2. Detectar huecos de fechas y crear placeholders.
3. Redescarga dirigida del período exacto faltante.
4. Interpolar lo que siga faltando, manteniendo el flag para reintentar.
"""
from __future__ import annotations

import sqlite3

from app.repositorios.velas import marcar_velas_en_cero


def marcar_corruptas(conexion: sqlite3.Connection) -> int:
    """Marca con es_faltante=1 las velas con precios inválidos. Devuelve cuántas."""
    return marcar_velas_en_cero(conexion)
