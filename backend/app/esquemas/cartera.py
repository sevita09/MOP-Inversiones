"""Modelos pydantic de las operaciones de cartera."""
from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field, model_validator

TipoOperacion = Literal["compra", "venta"]


class TransaccionPeticion(BaseModel):
    """Se carga con `precio` (unitario de mercado) O con `monto_final` (lo que
    cobró el broker). El que falte lo despeja el backend con la tasa vigente."""

    ticker: str
    tipo: TipoOperacion
    fecha: str  # AAAA-MM-DD, validada en el router contra el formato real
    cantidad: float = Field(gt=0)
    precio: Optional[float] = Field(default=None, gt=0)  # ARS por unidad
    monto_final: Optional[float] = Field(default=None, gt=0)  # ARS totales del resumen
    nota: str = ""

    @model_validator(mode="after")
    def _uno_de_los_dos(self) -> "TransaccionPeticion":
        if (self.precio is None) == (self.monto_final is None):
            raise ValueError("Indicá el precio unitario o el monto final, no ambos ni ninguno")
        return self


class TransaccionEdicion(BaseModel):
    """Edición parcial: solo se aplican los campos presentes."""

    ticker: Optional[str] = None
    tipo: Optional[TipoOperacion] = None
    fecha: Optional[str] = None
    cantidad: Optional[float] = Field(default=None, gt=0)
    precio: Optional[float] = Field(default=None, gt=0)
    monto_final: Optional[float] = Field(default=None, gt=0)
    nota: Optional[str] = None


class ComisionesPeticion(BaseModel):
    """Tasas del boleto del broker, en porcentaje (ver el resumen de la operación)."""

    arancel_pct: float = Field(ge=0, le=10)
    arancel_intradia_pct: float = Field(ge=0, le=10)
    derechos_mercado_pct: float = Field(ge=0, le=10)
    iva_pct: float = Field(ge=0, le=100)


class SplitPeticion(BaseModel):
    """Split de acciones: `ratio` son los papeles nuevos por cada papel viejo.

    Un split 3:1 es ratio 3 (tenías 100, pasás a tener 300).
    Un split inverso 1:10 es ratio 0.1 (tenías 100, pasás a tener 10).
    """

    ticker: str
    fecha: str  # AAAA-MM-DD, desde cuándo rige
    ratio: float = Field(gt=0)
    nota: str = ""
