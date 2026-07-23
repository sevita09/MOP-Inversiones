from __future__ import annotations

import sqlite3

from fastapi import APIRouter, Depends, HTTPException

from app.config import TICKERS_DOLAR
from app.db import conexion_api
from app.esquemas.bots import BotEdicion, BotPeticion, PlantillaPeticion, PreviewPeticion
from app.repositorios import bots as repo
from app.repositorios import plantillas as repo_plantillas
from app.repositorios import senales as repo_senales
from app.servicios.bots.evaluador import evaluar_reglas, temporalidades_de
from app.servicios.bots.plantillas import listar_plantillas
from app.servicios.dolar import velas_para_vista
from app.servicios.tickers_extra import universo_completo

router = APIRouter(prefix="/api")


def _validar_ticker(conexion: sqlite3.Connection, ticker: str) -> str:
    """Los bots operan cualquier ticker con datos, menos los de dólar."""
    ticker = ticker.upper()
    if ticker in TICKERS_DOLAR or ticker not in universo_completo(conexion):
        raise HTTPException(422, f"Ticker inválido para bots: {ticker}")
    return ticker


@router.get("/bots")
def listar_bots(conexion: sqlite3.Connection = Depends(conexion_api)):
    return repo.listar(conexion)


def _plantilla_propia_a_salida(plantilla: dict) -> dict:
    """Da a una plantilla del usuario la misma forma que las predefinidas."""
    return {
        "clave": f"custom:{plantilla['id']}",
        "id": plantilla["id"],
        "nombre": plantilla["nombre"],
        "descripcion": plantilla["descripcion"],
        "horizonte": "Plantilla propia",
        "temporalidad": plantilla["temporalidad"],
        "moneda": plantilla["moneda"],
        "reglas": plantilla["reglas"],
        "predefinida": False,
    }


@router.get("/bots/plantillas")
def plantillas_de_bots(conexion: sqlite3.Connection = Depends(conexion_api)):
    """Las 4 estrategias de la metodología + las plantillas propias del usuario."""
    predefinidas = [{**p, "id": None, "predefinida": True} for p in listar_plantillas()]
    propias = [_plantilla_propia_a_salida(p) for p in repo_plantillas.listar(conexion)]
    return predefinidas + propias


@router.post("/bots/plantillas", status_code=201)
def crear_plantilla(
    body: PlantillaPeticion, conexion: sqlite3.Connection = Depends(conexion_api)
):
    """Guarda una estrategia propia para reusarla como plantilla."""
    nombre = body.nombre.strip()
    if not nombre:
        raise HTTPException(422, "El nombre no puede estar vacío")
    if any(p["nombre"] == nombre for p in listar_plantillas()):
        raise HTTPException(409, f"Ya existe una plantilla de la metodología llamada {nombre}")
    creada = repo_plantillas.crear(
        conexion,
        nombre,
        body.descripcion.strip(),
        body.temporalidad,
        body.moneda,
        body.reglas.model_dump(exclude_none=True),
    )
    if creada is None:
        raise HTTPException(409, f"Ya existe una plantilla llamada {nombre}")
    return _plantilla_propia_a_salida(creada)


@router.delete("/bots/plantillas/{id_plantilla}")
def eliminar_plantilla(
    id_plantilla: int, conexion: sqlite3.Connection = Depends(conexion_api)
):
    if not repo_plantillas.eliminar(conexion, id_plantilla):
        raise HTTPException(404, "Plantilla no encontrada")
    return {"ok": True}


@router.post("/bots/preview")
def preview_de_reglas(
    body: PreviewPeticion, conexion: sqlite3.Connection = Depends(conexion_api)
):
    """Evalúa las reglas sobre la historia del ticker (las mismas velas e
    indicadores que ve el chart) y devuelve los ts donde disparan."""
    ticker = _validar_ticker(conexion, body.ticker)
    velas_por = {
        tf: velas_para_vista(conexion, ticker, tf, body.moneda)
        for tf in temporalidades_de(body.reglas, body.temporalidad)
    }
    try:
        return evaluar_reglas(velas_por, body.reglas, body.temporalidad)
    except ValueError as error:
        # Condición de temporalidad menor a la del bot (p.ej. D en un bot S)
        raise HTTPException(422, str(error))


@router.get("/bots/{id_bot}")
def obtener_bot(id_bot: int, conexion: sqlite3.Connection = Depends(conexion_api)):
    bot = repo.obtener(conexion, id_bot)
    if bot is None:
        raise HTTPException(404, "Bot no encontrado")
    return bot


@router.post("/bots", status_code=201)
def crear_bot(body: BotPeticion, conexion: sqlite3.Connection = Depends(conexion_api)):
    nombre = body.nombre.strip()
    if not nombre:
        raise HTTPException(422, "El nombre no puede estar vacío")
    ticker = _validar_ticker(conexion, body.ticker)
    bot = repo.crear(
        conexion,
        nombre,
        ticker,
        body.temporalidad,
        body.moneda,
        body.capital.model_dump(),
        body.reglas.model_dump(exclude_none=True) if body.reglas else None,
        activo=body.activo,
    )
    if bot is None:
        raise HTTPException(409, f"Ya existe un bot llamado {nombre}")
    return bot


@router.put("/bots/{id_bot}")
def editar_bot(
    id_bot: int, body: BotEdicion, conexion: sqlite3.Connection = Depends(conexion_api)
):
    cambios = body.model_dump(exclude_none=True)
    if "nombre" in cambios:
        cambios["nombre"] = cambios["nombre"].strip()
        if not cambios["nombre"]:
            raise HTTPException(422, "El nombre no puede estar vacío")
    if "ticker" in cambios:
        cambios["ticker"] = _validar_ticker(conexion, cambios["ticker"])
    bot = repo.actualizar(conexion, id_bot, cambios)
    if bot is False:
        raise HTTPException(404, "Bot no encontrado")
    if bot is None:
        raise HTTPException(409, f"Ya existe un bot llamado {cambios['nombre']}")
    return bot


@router.delete("/bots/{id_bot}")
def eliminar_bot(id_bot: int, conexion: sqlite3.Connection = Depends(conexion_api)):
    if not repo.eliminar(conexion, id_bot):
        raise HTTPException(404, "Bot no encontrado")
    repo_senales.borrar_de_bot(conexion, id_bot)  # sus señales se van con él
    return {"ok": True}


@router.post("/bots/{id_bot}/duplicar", status_code=201)
def duplicar_bot(id_bot: int, conexion: sqlite3.Connection = Depends(conexion_api)):
    copia = repo.duplicar(conexion, id_bot)
    if copia is None:
        raise HTTPException(404, "Bot no encontrado")
    return copia
