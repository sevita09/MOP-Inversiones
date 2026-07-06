#!/bin/bash
# Empaqueta MOP de punta a punta: build del frontend + PyInstaller + imagen .dmg
# lista para instalar arrastrando a Aplicaciones (con el ícono SV en el volumen).
# Uso: ./scripts/crear_dmg.sh   → deja el .dmg en backend/dist/
set -euo pipefail
RAIZ="$(cd "$(dirname "$0")/.." && pwd)"

echo "→ Build del frontend"
cd "$RAIZ/frontend" && npm run build

echo "→ Empaquetado con PyInstaller"
cd "$RAIZ/backend" && venv/bin/pyinstaller --noconfirm MOP.spec

VERSION=$(venv/bin/python -c "from app.version import VERSION; print(VERSION)")
APP="$RAIZ/backend/dist/MOP - Inversiones.app"
DMG="$RAIZ/backend/dist/MOP-Inversiones-v$VERSION.dmg"
VOLUMEN="MOP - Inversiones v$VERSION"

echo "→ Armando el .dmg v$VERSION"
ARMADO=$(mktemp -d)
cp -R "$APP" "$ARMADO/"
ln -s /Applications "$ARMADO/Applications"   # instalar = arrastrar el .app acá

# Imagen de lectura/escritura primero, para poder ponerle el ícono SV al volumen
CRUDO=$(mktemp -u).dmg
hdiutil create -volname "$VOLUMEN" -srcfolder "$ARMADO" -format UDRW -ov "$CRUDO" >/dev/null
PUNTO=$(hdiutil attach "$CRUDO" -nobrowse | awk -F'\t' '/\/Volumes\//{print $NF}')
cp "$RAIZ/backend/mop.icns" "$PUNTO/.VolumeIcon.icns"
if command -v SetFile >/dev/null; then
  SetFile -a C "$PUNTO"   # bit de "ícono propio" del volumen
fi
hdiutil detach "$PUNTO" >/dev/null

# Comprimir a la imagen final de solo lectura
rm -f "$DMG"
hdiutil convert "$CRUDO" -format UDZO -o "$DMG" >/dev/null
rm -f "$CRUDO"
rm -rf "$ARMADO"

echo "OK: $DMG"
