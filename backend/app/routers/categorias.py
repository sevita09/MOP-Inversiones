from __future__ import annotations

import sqlite3

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.config import CEDEARS, TICKERS_DOLAR, tickers_byma
from app.db import conexion_api
from app.repositorios import categorias as repo

router = APIRouter(prefix="/api")


def _tickers_validos() -> set[str]:
    return set(tickers_byma() + CEDEARS + TICKERS_DOLAR)


class CategoriaPeticion(BaseModel):
    nombre: str


class TickerPeticion(BaseModel):
    ticker: str


class FavoritosPeticion(BaseModel):
    tickers: list[str]


@router.get("/categorias")
def listar_categorias(conexion: sqlite3.Connection = Depends(conexion_api)):
    return repo.listar(conexion)


@router.post("/categorias", status_code=201)
def crear_categoria(
    body: CategoriaPeticion, conexion: sqlite3.Connection = Depends(conexion_api)
):
    nombre = body.nombre.strip()
    if not nombre:
        raise HTTPException(422, "El nombre no puede estar vacío")
    creada = repo.crear(conexion, nombre)
    if creada is None:
        raise HTTPException(409, f"Ya existe la categoría {nombre}")
    return creada


@router.delete("/categorias/{id_categoria}")
def eliminar_categoria(
    id_categoria: int, conexion: sqlite3.Connection = Depends(conexion_api)
):
    if not repo.eliminar(conexion, id_categoria):
        raise HTTPException(404, "Categoría no encontrada")
    return {"ok": True}


@router.post("/categorias/{id_categoria}/tickers", status_code=201)
def agregar_ticker(
    id_categoria: int,
    body: TickerPeticion,
    conexion: sqlite3.Connection = Depends(conexion_api),
):
    ticker = body.ticker.upper()
    if ticker not in _tickers_validos():
        raise HTTPException(422, f"Ticker desconocido: {ticker}")
    if not repo.agregar_ticker(conexion, id_categoria, ticker):
        raise HTTPException(404, "Categoría no encontrada")
    return {"ok": True}


@router.delete("/categorias/{id_categoria}/tickers/{ticker}")
def quitar_ticker(
    id_categoria: int, ticker: str, conexion: sqlite3.Connection = Depends(conexion_api)
):
    if not repo.quitar_ticker(conexion, id_categoria, ticker.upper()):
        raise HTTPException(404, "El ticker no está en esa categoría")
    return {"ok": True}


# --- favoritos (migrados de localStorage a la base) ---


@router.get("/favoritos")
def listar_favoritos(conexion: sqlite3.Connection = Depends(conexion_api)):
    return {"tickers": repo.listar_favoritos(conexion)}


@router.put("/favoritos")
def guardar_favoritos(
    body: FavoritosPeticion, conexion: sqlite3.Connection = Depends(conexion_api)
):
    validos = _tickers_validos()
    tickers = [t.upper() for t in body.tickers if t.upper() in validos]
    repo.reemplazar_favoritos(conexion, tickers)
    return {"tickers": tickers}
