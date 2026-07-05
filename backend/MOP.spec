# -*- mode: python ; coding: utf-8 -*-
# Empaqueta MOP como app de escritorio auto-contenida (.app).
# Build:  cd backend && venv/bin/pyinstaller --noconfirm MOP.spec
from pathlib import Path

RAIZ = Path(SPECPATH).parent                 # SPECPATH = backend/  →  raíz del repo
FRONTEND_DIST = str(RAIZ / "frontend" / "dist")

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
    name="MOP - Inversiones",
    console=False,           # app de ventana, sin terminal
    icon="mop.icns",
)
coll = COLLECT(exe, a.binaries, a.datas, name="MOP - Inversiones")
app = BUNDLE(
    coll,
    name="MOP - Inversiones.app",
    icon="mop.icns",
    bundle_identifier="com.sv.mop-inversiones",
    info_plist={
        "CFBundleName": "MOP - Inversiones",
        "CFBundleDisplayName": "MOP - Inversiones",
        "NSHighResolutionCapable": True,
    },
)
