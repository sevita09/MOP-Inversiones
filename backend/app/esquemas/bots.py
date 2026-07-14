"""Modelos pydantic de entrada para el CRUD de bots.

Las reglas viajan como dict libre hasta v4.2, que trae su esquema fuerte.
"""
from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field

Temporalidad = Literal["D", "S", "M"]
Moneda = Literal["ARS", "USD"]


class Capital(BaseModel):
    inicial: float = Field(default=1000000, gt=0)
    porcentaje_por_posicion: float = Field(default=100, gt=0, le=100)


class BotPeticion(BaseModel):
    nombre: str = Field(min_length=1)
    ticker: str
    temporalidad: Temporalidad
    moneda: Moneda = "ARS"
    capital: Capital = Capital()
    activo: bool = True


class BotEdicion(BaseModel):
    """Edición parcial: solo se aplican los campos presentes."""

    nombre: Optional[str] = Field(default=None, min_length=1)
    ticker: Optional[str] = None
    temporalidad: Optional[Temporalidad] = None
    moneda: Optional[Moneda] = None
    capital: Optional[Capital] = None
    activo: Optional[bool] = None
