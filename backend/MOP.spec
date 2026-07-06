# -*- mode: python ; coding: utf-8 -*-
# Empaqueta MOP como app de escritorio auto-contenida (.app).
# Build:  cd backend && venv/bin/pyinstaller --noconfirm MOP.spec
# Canal dev (ícono DEV, otro nombre): MOP_CANAL=dev vía scripts/crear_app_dev.sh
import os
from pathlib import Path

RAIZ = Path(SPECPATH).parent                 # SPECPATH = backend/  →  raíz del repo
FRONTEND_DIST = str(RAIZ / "frontend" / "dist")

DEV = os.environ.get("MOP_CANAL") == "dev"
NOMBRE = "MOP Dev" if DEV else "MOP - Inversiones"
ICONO = "mop-dev.icns" if DEV else "mop.icns"
BUNDLE_ID = "com.sv.mop-inversiones.dev" if DEV else "com.sv.mop-inversiones"

# uvicorn importa estos de forma dinámica; PyInstaller no los ve solo
UVICORN_HIDDEN = [
    "uvicorn.logging",
    "uvicorn.loops", "uvicorn.loops.auto",
    "uvicorn.protocols",
    "uvicorn.protocols.http", "uvicorn.protocols.http.auto",
    "uvicorn.protocols.websockets", "uvicorn.protocols.websockets.auto",
    "uvicorn.lifespan", "uvicorn.lifespan.on",
]

a = Analysis(
    ["escritorio.py"],
    pathex=[],
    binaries=[],
    datas=[(FRONTEND_DIST, "frontend/dist")],   # el frontend compilado viaja dentro del bundle
    hiddenimports=UVICORN_HIDDEN,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz, a.scripts, [],
    exclude_binaries=True,
    name=NOMBRE,
    console=False,           # app de ventana, sin terminal
    icon=ICONO,
)
coll = COLLECT(exe, a.binaries, a.datas, name=NOMBRE)
app = BUNDLE(
    coll,
    name=f"{NOMBRE}.app",
    icon=ICONO,
    bundle_identifier=BUNDLE_ID,
    info_plist={
        "CFBundleName": NOMBRE,
        "CFBundleDisplayName": NOMBRE,
        "NSHighResolutionCapable": True,
    },
)
