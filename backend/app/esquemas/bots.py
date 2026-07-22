"""Modelos pydantic de entrada para el CRUD y la vista previa de bots."""
from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field

from app.esquemas.reglas import Reglas

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
    reglas: Optional[Reglas] = None  # None ⇒ bloques vacíos (bot recién creado)
    activo: bool = True


class PreviewPeticion(BaseModel):
    """Vista previa de reglas: dónde disparan sobre la historia de un ticker."""

    ticker: str
    temporalidad: Temporalidad
    moneda: Moneda = "ARS"
    reglas: Reglas


class PlantillaPeticion(BaseModel):
    """Plantilla propia que el usuario guarda desde el editor."""

    nombre: str = Field(min_length=1)
    descripcion: str = ""
    temporalidad: Temporalidad = "D"
    moneda: Moneda = "USD"
    reglas: Reglas


class BotEdicion(BaseModel):
    """Edición parcial: solo se aplican los campos presentes."""

    nombre: Optional[str] = Field(default=None, min_length=1)
    ticker: Optional[str] = None
    temporalidad: Optional[Temporalidad] = None
    moneda: Optional[Moneda] = None
    capital: Optional[Capital] = None
    reglas: Optional[Reglas] = None
    activo: Optional[bool] = None
