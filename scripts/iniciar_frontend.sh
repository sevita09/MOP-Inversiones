#!/bin/bash
# Levanta el frontend de MOP en el puerto 5173
cd "$(dirname "$0")/../frontend" || exit 1

if [ ! -d node_modules ]; then
  echo "Instalando dependencias..."
  npm install
fi

npm run dev
