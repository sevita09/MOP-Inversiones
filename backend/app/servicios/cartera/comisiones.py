"""Gastos de la operación, con la estructura real del resumen del broker.

Un boleto de BYMA cobra tres cosas sobre el importe bruto:

    Arancel        0,1000%   →  lo del broker (0,05% si es compra-venta en el día)
    D. Mercado     0,0800%   →  derechos de mercado
    IVA           21,0000%   →  sobre la SUMA de los dos anteriores

    Importe neto = bruto ± (arancel + derechos + IVA)

Ejemplo real (compra de 5.000 papeles a $2.180):
    bruto     10.900.000,00
    arancel       10.900,00   (0,1%)
    d. mercado     8.720,00   (0,08%)
    IVA            4.120,20   (21% de 19.620)
    neto      10.923.740,20

Todas las tasas son configurables: si el broker cambia sus condiciones o cambia
el IVA, se ajustan sin tocar el código.

El usuario carga **cantidad + el importe neto** (lo que figura en el resumen) y
acá se despeja el precio de mercado y el desglose de gastos.
"""
from __future__ import annotations

import sqlite3
from typing import Optional

CLAVE_ARANCEL = "arancel_pct"
CLAVE_ARANCEL_INTRADIA = "arancel_intradia_pct"
CLAVE_DERECHOS = "derechos_mercado_pct"
CLAVE_IVA = "iva_pct"

DEFAULT_ARANCEL = 0.1
DEFAULT_ARANCEL_INTRADIA = 0.05
DEFAULT_DERECHOS = 0.08
DEFAULT_IVA = 21.0


def tasas(conexion: sqlite3.Connection) -> dict:
    from app.repositorios.configuracion import leer_numero

    return {
        "arancel_pct": leer_numero(conexion, CLAVE_ARANCEL, DEFAULT_ARANCEL),
        "arancel_intradia_pct": leer_numero(
            conexion, CLAVE_ARANCEL_INTRADIA, DEFAULT_ARANCEL_INTRADIA
        ),
        "derechos_mercado_pct": leer_numero(conexion, CLAVE_DERECHOS, DEFAULT_DERECHOS),
        "iva_pct": leer_numero(conexion, CLAVE_IVA, DEFAULT_IVA),
    }


def hay_operacion_opuesta(
    conexion: sqlite3.Connection,
    ticker: str,
    fecha: str,
    tipo: str,
    excluir_id: Optional[int] = None,
) -> bool:
    """¿Ya hay una operación del sentido contrario ese día sobre ese papel?"""
    opuesto = "venta" if tipo == "compra" else "compra"
    consulta = "SELECT 1 FROM transacciones WHERE ticker = ? AND fecha = ? AND tipo = ?"
    parametros: list = [ticker, fecha, opuesto]
    if excluir_id is not None:
        consulta += " AND id != ?"
        parametros.append(excluir_id)
    return conexion.execute(consulta + " LIMIT 1", parametros).fetchone() is not None


def tasa_efectiva(tasas_config: dict, es_intradia: bool) -> float:
    """% total de gastos sobre el bruto: (arancel + derechos) con su IVA."""
    arancel = (
        tasas_config["arancel_intradia_pct"] if es_intradia else tasas_config["arancel_pct"]
    )
    gastos = arancel + tasas_config["derechos_mercado_pct"]
    return gastos * (1 + tasas_config["iva_pct"] / 100)


def contexto(
    conexion: sqlite3.Connection,
    ticker: str,
    fecha: str,
    tipo: str,
    excluir_id: Optional[int] = None,
) -> dict:
    """Tasas y tasa efectiva que corresponden a esa operación."""
    config = tasas(conexion)
    es_intradia = hay_operacion_opuesta(conexion, ticker, fecha, tipo, excluir_id)
    return {
        **config,
        "es_intradia": es_intradia,
        "arancel_aplicado_pct": (
            config["arancel_intradia_pct"] if es_intradia else config["arancel_pct"]
        ),
        "tasa_efectiva_pct": round(tasa_efectiva(config, es_intradia), 6),
    }


def desglosar(bruto: float, config: dict, es_intradia: bool) -> dict:
    """Arancel, derechos, IVA y total de gastos sobre un importe bruto."""
    arancel_pct = (
        config["arancel_intradia_pct"] if es_intradia else config["arancel_pct"]
    )
    arancel = bruto * arancel_pct / 100
    derechos = bruto * config["derechos_mercado_pct"] / 100
    iva = (arancel + derechos) * config["iva_pct"] / 100
    return {
        "arancel": round(arancel, 2),
        "derechos_mercado": round(derechos, 2),
        "iva": round(iva, 2),
        "gastos": round(arancel + derechos + iva, 2),
    }


def desde_monto_final(
    monto_final: float, cantidad: float, tipo: str, config: dict, es_intradia: bool
) -> dict:
    """Despeja el precio de mercado desde el importe neto del resumen."""
    tasa = tasa_efectiva(config, es_intradia) / 100
    factor = 1 + tasa if tipo == "compra" else 1 - tasa
    if factor <= 0 or cantidad <= 0:
        raise ValueError("Tasas o cantidad inválidas para despejar el precio")
    bruto = monto_final / factor
    return {
        "precio": round(bruto / cantidad, 6),
        "bruto": round(bruto, 2),
        **desglosar(bruto, config, es_intradia),
    }


def desde_precio(
    precio: float, cantidad: float, tipo: str, config: dict, es_intradia: bool
) -> dict:
    """Camino inverso: del precio de mercado al importe neto del resumen."""
    bruto = precio * cantidad
    desglose = desglosar(bruto, config, es_intradia)
    neto = bruto + desglose["gastos"] if tipo == "compra" else bruto - desglose["gastos"]
    return {"bruto": round(bruto, 2), "monto_final": round(neto, 2), **desglose}
