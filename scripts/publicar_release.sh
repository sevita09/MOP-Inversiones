#!/bin/bash
# Publica la versión actual como release de GitHub con el .dmg adjunto.
# El asset descargable es lo que usa la auto-actualización (v3.4).
# Requiere: el tag vX.Y.Z ya pusheado y el .dmg generado (scripts/crear_dmg.sh).
# El token sale del llavero de git (el mismo que usa git push).
set -euo pipefail
RAIZ="$(cd "$(dirname "$0")/.." && pwd)"
REPO="sevita09/MOP-Inversiones"

# El import de app.version necesita correr parado en backend/
VERSION=$(cd "$RAIZ/backend" && venv/bin/python -c "from app.version import VERSION; print(VERSION)")
TAG="v$VERSION"
DMG="$RAIZ/backend/dist/MOP-Inversiones-v$VERSION.dmg"

[ -f "$DMG" ] || { echo "Falta $DMG — correr scripts/crear_dmg.sh primero"; exit 1; }
git -C "$RAIZ" rev-parse "$TAG" >/dev/null 2>&1 || { echo "El tag $TAG no existe — cerrar la versión primero"; exit 1; }

TOKEN=$(printf "protocol=https\nhost=github.com\n" | git credential fill | sed -n 's/^password=//p')
[ -n "$TOKEN" ] || { echo "Sin token de GitHub en el llavero de git"; exit 1; }

API="https://api.github.com/repos/$REPO"
AUTH="Authorization: Bearer $TOKEN"

# Nombre de la release = mensaje del tag anotado ("vX.Y.Z — Nombre")
NOMBRE=$(git -C "$RAIZ" tag -l --format='%(contents:subject)' "$TAG")

# Reutilizar la release si ya existe; si no, crearla sobre el tag
ID=$(curl -sf -H "$AUTH" "$API/releases/tags/$TAG" 2>/dev/null \
     | "$RAIZ/backend/venv/bin/python" -c "import sys,json; print(json.load(sys.stdin)['id'])" 2>/dev/null || true)
if [ -z "$ID" ]; then
  ID=$(curl -sf -X POST -H "$AUTH" -d "{\"tag_name\":\"$TAG\",\"name\":\"$NOMBRE\"}" "$API/releases" \
       | "$RAIZ/backend/venv/bin/python" -c "import sys,json; print(json.load(sys.stdin)['id'])")
  echo "→ Release creada: $NOMBRE"
else
  echo "→ Release existente para $TAG (id $ID)"
fi

echo "→ Subiendo $(basename "$DMG") ($(du -h "$DMG" | cut -f1 | tr -d ' '))"
SUBIDA="https://uploads.github.com/repos/$REPO/releases/$ID/assets?name=$(basename "$DMG")"
curl -sf -X POST -H "$AUTH" -H "Content-Type: application/octet-stream" \
     --data-binary @"$DMG" "$SUBIDA" >/dev/null

echo "OK: https://github.com/$REPO/releases/tag/$TAG"
