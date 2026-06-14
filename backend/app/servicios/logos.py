"""Descarga de logos de tickers desde TradingView, cacheados en disco.

Flujo: scanner de TradingView devuelve el `logoid` del símbolo; el logo vive en
el CDN `s3-symbol-logo.tradingview.com/<logoid>.svg`. Se baja una sola vez por
ticker y se guarda en `logos/<TICKER>.svg`. `asegurar_logos()` baja solo los que
falten, así un ticker nuevo agregado al código se completa solo al arrancar.
"""
from __future__ import annotations

import threading
import time
from pathlib import Path
from typing import Optional

import httpx

from app.config import CEDEARS, tickers_byma

CARPETA_LOGOS = Path(__file__).resolve().parents[2] / "logos"

URL_SCANNER = "https://scanner.tradingview.com/symbol"
URL_CDN = "https://s3-symbol-logo.tradingview.com"
ENCABEZADOS = {"User-Agent": "Mozilla/5.0"}

# Exchange de cada CEDEAR/ADR en TradingView (BYMA usa siempre BCBA)
EXCHANGE_CEDEARS = {"AAPL": "NASDAQ"}


def tickers_con_logo() -> list[str]:
    """Tickers que pueden tener logo en TradingView (los de dólar quedan afuera)."""
    return tickers_byma() + CEDEARS


def simbolo_tradingview(ticker: str) -> Optional[str]:
    """Símbolo EXCHANGE:TICKER para TradingView, o None si el ticker no aplica."""
    if ticker in tickers_byma():
        return f"BCBA:{ticker}"
    if ticker in CEDEARS:
        return f"{EXCHANGE_CEDEARS.get(ticker, 'NASDAQ')}:{ticker}"
    return None


def ruta_logo(ticker: str) -> Path:
    return CARPETA_LOGOS / f"{ticker}.svg"


def tiene_logo(ticker: str) -> bool:
    return ruta_logo(ticker).exists()


def obtener_logoid(ticker: str, cliente: httpx.Client) -> Optional[str]:
    """Consulta el scanner de TradingView por el logoid del símbolo."""
    simbolo = simbolo_tradingview(ticker)
    if simbolo is None:
        return None
    respuesta = cliente.get(
        URL_SCANNER, params={"symbol": simbolo, "fields": "logoid"}, headers=ENCABEZADOS
    )
    respuesta.raise_for_status()
    logoid = respuesta.json().get("logoid")
    return logoid or None


def descargar_logo(ticker: str, cliente: httpx.Client) -> bool:
    """Baja el logo del ticker y lo guarda en disco. Devuelve si lo consiguió."""
    logoid = obtener_logoid(ticker, cliente)
    if not logoid:
        return False
    respuesta = cliente.get(f"{URL_CDN}/{logoid}.svg", headers=ENCABEZADOS)
    if respuesta.status_code != 200:
        return False
    CARPETA_LOGOS.mkdir(exist_ok=True)
    ruta_logo(ticker).write_bytes(respuesta.content)
    return True


def asegurar_logos(pausa: float = 0.2) -> int:
    """Baja los logos faltantes de todos los tickers. Devuelve cuántos bajó."""
    faltantes = [t for t in tickers_con_logo() if not tiene_logo(t)]
    if not faltantes:
        return 0
    bajados = 0
    with httpx.Client(timeout=15) as cliente:
        for ticker in faltantes:
            try:
                if descargar_logo(ticker, cliente):
                    bajados += 1
            except Exception:
                continue  # un ticker que falla no frena al resto
            time.sleep(pausa)  # no martillar a TradingView
    return bajados


def asegurar_logos_en_background() -> None:
    """Lanza asegurar_logos en un thread aparte (no bloquea el arranque)."""
    threading.Thread(target=asegurar_logos, name="logos-mop", daemon=True).start()
