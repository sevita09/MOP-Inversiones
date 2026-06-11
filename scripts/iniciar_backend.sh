#!/bin/bash
# Levanta el backend de MOP en el puerto 8000
cd "$(dirname "$0")/../backend" || exit 1

if [ ! -d venv ]; then
  echo "Creando entorno virtual..."
  python3 -m venv venv
  source venv/bin/activate
  pip install -r requirements.txt
else
  source venv/bin/activate
fi

uvicorn app.main:app --reload --port 8000
