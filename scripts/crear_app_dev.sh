#!/bin/bash
# Construye e instala "MOP Dev": la app de pruebas, separada de la productiva.
# Ícono con cinta DEV, puerto 8100, datos en ~/Library/Application Support/MOP Dev,
# sin auto-actualización. Conviven en el dock sin pisarse.
# Uso: ./scripts/crear_app_dev.sh
set -euo pipefail
RAIZ="$(cd "$(dirname "$0")/.." && pwd)"

echo "→ Build del frontend"
cd "$RAIZ/frontend" && npm run build

echo "→ Empaquetado del canal dev"
cd "$RAIZ/backend"
cp app/canal.py /tmp/mop_canal_original.py
trap 'cp /tmp/mop_canal_original.py "$RAIZ/backend/app/canal.py"' EXIT  # restaurar siempre
sed -i '' 's/^CANAL = .*/CANAL = "dev"/' app/canal.py
MOP_CANAL=dev venv/bin/pyinstaller --noconfirm MOP.spec

echo "→ Instalando MOP Dev en /Applications"
rm -rf "/Applications/MOP Dev.app"
cp -R "dist/MOP Dev.app" /Applications/

# Semilla de datos: si el canal dev arranca sin base, copiar la del repo
DATOS_DEV="$HOME/Library/Application Support/MOP Dev"
if [ ! -f "$DATOS_DEV/mop.db" ] && [ -f "$RAIZ/mop.db" ]; then
  mkdir -p "$DATOS_DEV"
  cp "$RAIZ/mop.db" "$DATOS_DEV/mop.db"
  echo "→ Base sembrada desde el repo (después vive su propia vida)"
fi

echo "OK: /Applications/MOP Dev.app (puerto 8100, datos en 'MOP Dev')"
