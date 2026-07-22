"""Esquema declarativo de reglas de bots (versión 1).

Una regla es un bloque de condiciones que se combinan con AND. Cada condición
compara una serie de un indicador del registry contra una constante, contra
otra serie del mismo indicador, o contra el precio (cierre):

    {"indicador": "bandas", "serie": "z", "operador": "menor", "objetivo": -2}
    {"indicador": "estocastico", "serie": "k", "operador": "cruza_arriba",
     "objetivo": {"serie": "d"}}
    {"indicador": "bandas", "serie": "media", "operador": "cruza_abajo_precio"}

Los operadores `cruza_*_precio` no llevan objetivo: el precio es quien cruza la
serie de la condición. `params` ajusta los parámetros del indicador (p.ej. una
EMA 20 en vez de la default); en `objetivo.params` permite cruzar dos variantes
del mismo indicador (EMA rápida × EMA lenta).

La temporalidad por condición llega en v4.4 (confluencia): hasta entonces todas
las condiciones se evalúan en la temporalidad del bot.
"""
from __future__ import annotations

from typing import Literal, Optional, Union

from pydantic import BaseModel, Field, field_validator, model_validator

# Series que expone cada indicador del registry. Estático a propósito (los
# nombres salen de correr cada función); test_esquema_reglas verifica que
# coincida con lo que el registry devuelve de verdad.
SERIES_POR_INDICADOR = {
    "ema": ("ema",),
    "z_score": ("z",),
    "rsi": ("rsi",),
    "macd": ("macd", "senal", "histograma"),
    "estocastico": ("k", "d"),
    "bandas": ("media", "sup1", "sup2", "sup3", "inf1", "inf2", "inf3", "z"),
    "bollinger": ("media", "superior", "inferior"),
    "atr": ("atr",),
    "porcentaje_b": ("porcentaje_b",),
    "adx": ("adx",),
    "percentil_distancia": ("percentil",),
}

Operador = Literal[
    "mayor",
    "menor",
    "cruza_arriba",
    "cruza_abajo",
    "cruza_arriba_precio",
    "cruza_abajo_precio",
]

OPERADORES_PRECIO = ("cruza_arriba_precio", "cruza_abajo_precio")

# Rango posible de las series acotadas: un umbral fuera de acá es incoherente
# (estocástico < −5 no dispara nunca; < 150 dispara siempre). El z-score no
# está acotado, pero ±10σ ya es físicamente irreal.
RANGO_SERIES = {
    ("estocastico", "k"): (0, 100),
    ("estocastico", "d"): (0, 100),
    ("rsi", "rsi"): (0, 100),
    ("adx", "adx"): (0, 100),
    ("percentil_distancia", "percentil"): (0, 100),
    ("bandas", "z"): (-10, 10),
    ("z_score", "z"): (-10, 10),
}


class ObjetivoSerie(BaseModel):
    """Otra serie del mismo indicador; `params` permite otra variante (EMA lenta)."""

    serie: str
    params: Optional[dict[str, float]] = None


class Condicion(BaseModel):
    indicador: str
    serie: str
    operador: Operador
    objetivo: Optional[Union[float, ObjetivoSerie]] = None
    params: Optional[dict[str, float]] = None
    # Confluencia (v4.4): la condición puede mirar OTRA temporalidad (superior a
    # la del bot). None ⇒ la del bot. La horaria queda fuera de los bots.
    temporalidad: Optional[Literal["D", "S", "M"]] = None

    @field_validator("indicador")
    @classmethod
    def _indicador_conocido(cls, valor: str) -> str:
        if valor not in SERIES_POR_INDICADOR:
            raise ValueError(f"Indicador desconocido: {valor}")
        return valor

    @model_validator(mode="after")
    def _coherencia(self) -> "Condicion":
        series = SERIES_POR_INDICADOR[self.indicador]
        if self.serie not in series:
            raise ValueError(
                f"El indicador {self.indicador} no tiene la serie {self.serie} "
                f"(tiene: {', '.join(series)})"
            )
        if self.operador in OPERADORES_PRECIO:
            if self.objetivo is not None:
                raise ValueError(f"{self.operador} no lleva objetivo: el precio cruza la serie")
        else:
            if self.objetivo is None:
                raise ValueError(f"El operador {self.operador} necesita un objetivo")
        if isinstance(self.objetivo, ObjetivoSerie):
            if self.objetivo.serie not in series:
                raise ValueError(
                    f"El objetivo {self.objetivo.serie} no es una serie de {self.indicador}"
                )
            # Cruzar una serie consigo misma (mismos parámetros) no dispara nunca;
            # con parámetros distintos sí vale (EMA rápida × EMA lenta)
            mismos_params = self.objetivo.params is None or self.objetivo.params == self.params
            if self.objetivo.serie == self.serie and mismos_params:
                raise ValueError(
                    f"Cruzar {self.serie} consigo misma no dispara nunca "
                    "(usá otra serie u otros parámetros)"
                )
        if isinstance(self.objetivo, (int, float)):
            rango = RANGO_SERIES.get((self.indicador, self.serie))
            if rango and not (rango[0] <= self.objetivo <= rango[1]):
                raise ValueError(
                    f"Umbral imposible: {self.indicador}.{self.serie} se mueve "
                    f"entre {rango[0]} y {rango[1]} (recibí {self.objetivo})"
                )
        return self


class Reglas(BaseModel):
    """`entrada` y `filtros` se combinan con AND para comprar; `salida` para vender."""

    version: Literal[1]
    entrada: list[Condicion] = Field(default_factory=list)
    salida: list[Condicion] = Field(default_factory=list)
    filtros: list[Condicion] = Field(default_factory=list)

    @model_validator(mode="after")
    def _entrada_presente(self) -> "Reglas":
        # Todo vacío vale (bot recién creado); salida o filtros sin entrada, no:
        # un bot que solo sabe vender no puede disparar nunca
        if not self.entrada and (self.salida or self.filtros):
            raise ValueError("Faltan las condiciones de entrada: sin entrada no hay señal")
        return self
