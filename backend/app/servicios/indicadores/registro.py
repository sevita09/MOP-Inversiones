"""Registro extensible de indicadores técnicos.

Agregar un indicador nuevo = una línea en su módulo (`registrar(...)`) + su
función + su test. Cada función recibe un DataFrame de velas (columnas:
apertura, maximo, minimo, cierre, volumen) y devuelve un dict
`{nombre_serie: pd.Series}` alineado al índice del DataFrame.
`calcular()` convierte esas series a listas JSON (NaN del warmup → None).
"""
from __future__ import annotations

import math
from typing import Callable

import pandas as pd

# nombre -> (función, params_default)
Indicador = Callable[..., "dict[str, pd.Series]"]
_REGISTRO: "dict[str, tuple[Indicador, dict]]" = {}


def registrar(nombre: str, funcion: Indicador, params_default: dict | None = None) -> None:
    _REGISTRO[nombre] = (funcion, params_default or {})


def disponibles() -> list[str]:
    return sorted(_REGISTRO)


def defaults_de(nombre: str) -> dict:
    """Parámetros por default de un indicador (para validar/coercer overrides)."""
    if nombre not in _REGISTRO:
        raise KeyError(f"Indicador desconocido: {nombre}")
    return dict(_REGISTRO[nombre][1])


def velas_a_df(velas: list[dict]) -> pd.DataFrame:
    columnas = ["ts", "apertura", "maximo", "minimo", "cierre", "volumen"]
    return pd.DataFrame(velas, columns=columnas)


def _serie_json(serie: pd.Series) -> list:
    # NaN/inf → None: JSON estándar no los admite y el navegador los rechaza
    return [
        None if pd.isna(valor) or not math.isfinite(float(valor)) else round(float(valor), 6)
        for valor in serie
    ]


def calcular(nombre: str, velas: list[dict], **params) -> dict[str, list]:
    if nombre not in _REGISTRO:
        raise KeyError(f"Indicador desconocido: {nombre}")
    funcion, defaults = _REGISTRO[nombre]
    salida = funcion(velas_a_df(velas), **{**defaults, **params})
    return {clave: _serie_json(serie) for clave, serie in salida.items()}
