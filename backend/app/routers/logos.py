from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from app.servicios.logos import ruta_logo, tiene_logo

router = APIRouter(prefix="/api")


@router.get("/logo/{ticker}")
def logo(ticker: str):
    ticker = ticker.upper()
    if not tiene_logo(ticker):
        raise HTTPException(404, f"Sin logo para {ticker}")
    return FileResponse(ruta_logo(ticker), media_type="image/svg+xml")
