#!/usr/bin/env python3
"""Genera los íconos de la app desde el logo con fondo transparente.

    ./scripts/crear_iconos.py

Produce `backend/mop.icns` (canal prod) y `backend/mop-dev.icns` (canal dev, con
la cinta naranja). El origen es `backend/mop-logo.png`: un PNG de 1024 con
transparencia, que se versiona para poder rehacer los íconos sin depender de
ningún editor.

Los `.icns` son binarios: si se pierden, se regeneran de acá.
"""
import os
import shutil
import subprocess
import sys
import tempfile

from PIL import Image, ImageDraw, ImageFont

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ORIGEN = os.path.join(RAIZ, "backend", "mop-logo.png")

# Los tamaños que macOS espera dentro de un .iconset (nombre → lado en píxeles)
TAMANOS = [
    ("icon_16x16", 16), ("icon_16x16@2x", 32),
    ("icon_32x32", 32), ("icon_32x32@2x", 64),
    ("icon_128x128", 128), ("icon_128x128@2x", 256),
    ("icon_256x256", 256), ("icon_256x256@2x", 512),
    ("icon_512x512", 512), ("icon_512x512@2x", 1024),
]

NARANJA = (232, 132, 58, 255)
FUENTE = "/System/Library/Fonts/Supplemental/Arial Bold.ttf"


def con_cinta_dev(logo: Image.Image) -> Image.Image:
    """El mismo logo con la cinta naranja: MOP Dev convive en el dock con la
    productiva y hay que poder distinguirlas de un vistazo."""
    lado = logo.size[0]
    salida = logo.copy()
    alto = int(lado * 0.26)
    ancho = int(lado * 0.82)
    x0 = (lado - ancho) // 2
    y0 = lado - alto - int(lado * 0.06)

    cinta = Image.new("RGBA", (lado, lado), (0, 0, 0, 0))
    dibujo = ImageDraw.Draw(cinta)
    dibujo.rounded_rectangle(
        [x0, y0, x0 + ancho, y0 + alto], radius=int(alto * 0.34), fill=NARANJA
    )
    fuente = ImageFont.truetype(FUENTE, int(alto * 0.62))
    caja = dibujo.textbbox((0, 0), "DEV", font=fuente)
    dibujo.text(
        (lado / 2 - (caja[2] - caja[0]) / 2, y0 + alto / 2 - (caja[3] - caja[1]) / 2 - caja[1]),
        "DEV",
        font=fuente,
        fill=(255, 255, 255, 255),
    )
    return Image.alpha_composite(salida, cinta)


def crear_icns(logo: Image.Image, destino: str) -> None:
    carpeta = tempfile.mkdtemp()
    conjunto = os.path.join(carpeta, "icono.iconset")
    os.makedirs(conjunto)
    for nombre, lado in TAMANOS:
        logo.resize((lado, lado), Image.LANCZOS).save(
            os.path.join(conjunto, f"{nombre}.png")
        )
    subprocess.run(
        ["iconutil", "-c", "icns", conjunto, "-o", destino], check=True
    )
    shutil.rmtree(carpeta)
    print(f"OK: {destino}")


def main() -> int:
    if not os.path.exists(ORIGEN):
        print(f"Falta el logo de origen: {ORIGEN}", file=sys.stderr)
        return 1
    logo = Image.open(ORIGEN).convert("RGBA")
    if logo.size != (1024, 1024):
        logo = logo.resize((1024, 1024), Image.LANCZOS)

    crear_icns(logo, os.path.join(RAIZ, "backend", "mop.icns"))
    crear_icns(con_cinta_dev(logo), os.path.join(RAIZ, "backend", "mop-dev.icns"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
