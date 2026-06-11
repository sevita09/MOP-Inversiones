#!/bin/bash
# Doble click: levanta backend y frontend de MOP y abre el navegador
RAIZ="$(cd "$(dirname "$0")" && pwd)"

"$RAIZ/scripts/iniciar_backend.sh" &
BACKEND_PID=$!
trap 'kill $BACKEND_PID 2>/dev/null' EXIT

sleep 2
open http://localhost:5173

"$RAIZ/scripts/iniciar_frontend.sh"
