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


class Riesgo(BaseModel):
    """Gestión de riesgo del backtest. Todo opcional: sin nada, opera como v5.2."""

    stop_loss_pct: Optional[float] = Field(default=None, gt=0, le=100)  # % bajo la entrada
    stop_atr_mult: Optional[float] = Field(default=None, gt=0)  # stop a N ATR bajo la entrada
    take_profit_pct: Optional[float] = Field(default=None, gt=0)  # % sobre la entrada
    salida_ema_central: bool = False  # salir al cruzar la EMA central hacia abajo
    trailing_pct: Optional[float] = Field(default=None, gt=0, le=100)  # trailing % desde el máximo
    atr_periodo: int = Field(default=14, ge=2, le=200)
    # Si está, el tamaño se calcula para arriesgar ese % del capital hasta el stop
    sizing_riesgo_pct: Optional[float] = Field(default=None, gt=0, le=100)


class BotPeticion(BaseModel):
    nombre: str = Field(min_length=1)
    ticker: str
    temporalidad: Temporalidad
    moneda: Moneda = "ARS"
    capital: Capital = Capital()
    riesgo: Riesgo = Riesgo()
    reglas: Optional[Reglas] = None  # None ⇒ bloques vacíos (bot recién creado)
    activo: bool = True


class PreviewPeticion(BaseModel):
    """Vista previa de reglas: dónde disparan sobre la historia de un ticker."""

    ticker: str
    temporalidad: Temporalidad
    moneda: Moneda = "ARS"
    reglas: Reglas


class PresetRiesgoPeticion(BaseModel):
    """Guardar una config de riesgo como preset reutilizable."""

    nombre: str = Field(min_length=1)
    riesgo: Riesgo


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
    riesgo: Optional[Riesgo] = None
    reglas: Optional[Reglas] = None
    activo: Optional[bool] = None
