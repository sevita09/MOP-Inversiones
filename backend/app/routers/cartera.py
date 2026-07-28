from __future__ import annotations

import sqlite3
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException

from app.db import conexion_api
from app.esquemas.cartera import (
    ComisionesPeticion,
    SplitPeticion,
    TransaccionEdicion,
    TransaccionPeticion,
)
from app.repositorios import configuracion as repo_config
from app.repositorios import splits as repo_splits
from app.repositorios import transacciones as repo
from app.servicios.cartera.comisiones import (
    CLAVE_ARANCEL,
    CLAVE_ARANCEL_INTRADIA,
    CLAVE_DERECHOS,
    CLAVE_IVA,
    contexto,
    desde_monto_final,
    desde_precio,
    tasas,
)
from app.servicios.cartera.posiciones import (
    cantidades_en_cartera,
    lotes_abiertos,
    tenencias,
)
from app.servicios.cartera.transacciones import enriquecer, fecha_valida, precio_sugerido
from app.servicios.tickers_extra import universo_completo

router = APIRouter(prefix="/api/cartera")


def _validar(conexion: sqlite3.Connection, ticker: str, fecha: str) -> str:
    """Ticker del universo y fecha con formato AAAA-MM-DD."""
    ticker = ticker.upper()
    if ticker not in universo_completo(conexion):
        raise HTTPException(422, f"Ticker desconocido: {ticker}")
    if not fecha_valida(fecha):
        raise HTTPException(422, f"Fecha inválida: {fecha} (usar AAAA-MM-DD)")
    return ticker


def _precio_y_comision(
    conexion: sqlite3.Connection,
    ticker: str,
    fecha: str,
    tipo: str,
    cantidad: float,
    precio: Optional[float],
    monto_final: Optional[float],
    excluir_id: Optional[int] = None,
) -> tuple[float, float]:
    """Despeja el par (precio unitario, comisión) desde lo que haya cargado."""
    ctx = contexto(conexion, ticker, fecha, tipo, excluir_id)
    try:
        if monto_final is not None:
            calculo = desde_monto_final(monto_final, cantidad, tipo, ctx, ctx["es_intradia"])
            return calculo["precio"], calculo["gastos"]
        calculo = desde_precio(precio, cantidad, tipo, ctx, ctx["es_intradia"])
        return precio, calculo["gastos"]
    except ValueError as error:
        raise HTTPException(422, str(error))


# --- comisiones ---


@router.get("/comisiones")
def obtener_comisiones(conexion: sqlite3.Connection = Depends(conexion_api)):
    """Tasas configuradas del broker (normal e intradía), en porcentaje."""
    return tasas(conexion)


@router.put("/comisiones")
def guardar_comisiones(
    body: ComisionesPeticion, conexion: sqlite3.Connection = Depends(conexion_api)
):
    repo_config.guardar(conexion, CLAVE_ARANCEL, body.arancel_pct)
    repo_config.guardar(conexion, CLAVE_ARANCEL_INTRADIA, body.arancel_intradia_pct)
    repo_config.guardar(conexion, CLAVE_DERECHOS, body.derechos_mercado_pct)
    repo_config.guardar(conexion, CLAVE_IVA, body.iva_pct)
    return tasas(conexion)


@router.get("/tasa_vigente")
def consultar_tasa(
    ticker: str,
    fecha: str,
    tipo: str,
    conexion: sqlite3.Connection = Depends(conexion_api),
):
    """Tasas que corresponden a esa operación y si se detectó intradía."""
    ticker = _validar(conexion, ticker, fecha)
    return contexto(conexion, ticker, fecha, tipo)


# --- splits ---


@router.get("/splits")
def listar_splits(
    ticker: Optional[str] = None, conexion: sqlite3.Connection = Depends(conexion_api)
):
    return repo_splits.listar(conexion, ticker.upper() if ticker else None)


@router.post("/splits", status_code=201)
def crear_split(body: SplitPeticion, conexion: sqlite3.Connection = Depends(conexion_api)):
    """Registra un split; recalcula sola la posición (no mueve plata)."""
    ticker = _validar(conexion, body.ticker, body.fecha)
    creado = repo_splits.crear(conexion, ticker, body.fecha, body.ratio, body.nota.strip())
    if creado is None:
        raise HTTPException(409, f"Ya hay un split de {ticker} en esa fecha")
    return creado


@router.delete("/splits/{id_split}")
def eliminar_split(id_split: int, conexion: sqlite3.Connection = Depends(conexion_api)):
    if not repo_splits.eliminar(conexion, id_split):
        raise HTTPException(404, "Split no encontrado")
    return {"ok": True}


# --- operaciones ---


@router.get("/tenencias")
def listar_tenencias(conexion: sqlite3.Connection = Depends(conexion_api)):
    """Posiciones abiertas por FIFO, con su P&L no realizado y los totales."""
    return tenencias(conexion)


@router.get("/lotes")
def lotes_de_un_papel(
    ticker: str, moneda: str = "ARS", conexion: sqlite3.Connection = Depends(conexion_api)
):
    """Compras abiertas de un papel con su PPC, para marcarlas en el gráfico.

    En USD cada compra se convierte con el CCL de su fecha.
    """
    if moneda not in ("ARS", "USD"):
        raise HTTPException(422, f"Moneda inválida: {moneda}")
    return lotes_abiertos(conexion, ticker.upper(), moneda)


@router.get("/en_cartera")
def papeles_en_cartera(conexion: sqlite3.Connection = Depends(conexion_api)):
    """Cantidad disponible por ticker: lo que se puede vender hoy."""
    return cantidades_en_cartera(conexion)


@router.get("/precio_sugerido")
def sugerir_precio(
    ticker: str, fecha: str, conexion: sqlite3.Connection = Depends(conexion_api)
):
    """Cierre de esa rueda en ARS, para precargar el precio de la operación."""
    ticker = _validar(conexion, ticker, fecha)
    return {"ticker": ticker, "fecha": fecha, "precio": precio_sugerido(conexion, ticker, fecha)}


@router.get("/transacciones")
def listar_transacciones(
    ticker: Optional[str] = None, conexion: sqlite3.Connection = Depends(conexion_api)
):
    """Historial de operaciones, más nuevas primero."""
    operaciones = repo.listar(conexion, ticker.upper() if ticker else None)
    return [enriquecer(conexion, operacion) for operacion in operaciones]


@router.post("/transacciones", status_code=201)
def crear_transaccion(
    body: TransaccionPeticion, conexion: sqlite3.Connection = Depends(conexion_api)
):
    ticker = _validar(conexion, body.ticker, body.fecha)
    precio, comision = _precio_y_comision(
        conexion, ticker, body.fecha, body.tipo, body.cantidad, body.precio, body.monto_final
    )
    creada = repo.crear(
        conexion, ticker, body.tipo, body.fecha, body.cantidad, precio, comision, body.nota.strip()
    )
    return enriquecer(conexion, creada)


@router.put("/transacciones/{id_transaccion}")
def editar_transaccion(
    id_transaccion: int,
    body: TransaccionEdicion,
    conexion: sqlite3.Connection = Depends(conexion_api),
):
    actual = repo.obtener(conexion, id_transaccion)
    if actual is None:
        raise HTTPException(404, "Operación no encontrada")

    cambios = body.model_dump(exclude_none=True)
    if "fecha" in cambios and not fecha_valida(cambios["fecha"]):
        raise HTTPException(422, f"Fecha inválida: {cambios['fecha']} (usar AAAA-MM-DD)")
    if "ticker" in cambios:
        ticker = cambios["ticker"].upper()
        if ticker not in universo_completo(conexion):
            raise HTTPException(422, f"Ticker desconocido: {ticker}")
        cambios["ticker"] = ticker

    # Si cambió algo que afecta el cálculo, recalcular precio y comisión juntos
    afecta = {"cantidad", "precio", "monto_final", "tipo", "fecha", "ticker"} & set(cambios)
    if afecta:
        futura = {**actual, **cambios}
        if "monto_final" in cambios:
            precio_entrada, monto_entrada = None, cambios["monto_final"]
        elif "precio" in cambios:
            precio_entrada, monto_entrada = cambios["precio"], None
        else:
            # Cambió cantidad/fecha/tipo: se conserva el precio y se recalcula la comisión
            precio_entrada, monto_entrada = actual["precio"], None
        precio, comision = _precio_y_comision(
            conexion,
            futura["ticker"],
            futura["fecha"],
            futura["tipo"],
            futura["cantidad"],
            precio_entrada,
            monto_entrada,
            excluir_id=id_transaccion,
        )
        cambios["precio"] = precio
        cambios["comision"] = comision
    cambios.pop("monto_final", None)  # no es columna: se deriva

    editada = repo.actualizar(conexion, id_transaccion, cambios)
    return enriquecer(conexion, editada)


@router.delete("/transacciones/{id_transaccion}")
def eliminar_transaccion(
    id_transaccion: int, conexion: sqlite3.Connection = Depends(conexion_api)
):
    if not repo.eliminar(conexion, id_transaccion):
        raise HTTPException(404, "Operación no encontrada")
    return {"ok": True}
