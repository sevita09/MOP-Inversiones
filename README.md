<p align="center">
  <img src="frontend/public/sv-logo.png" width="120" alt="MOP Inversiones">
</p>

# MOP - Inversiones

Plataforma personal de análisis e inversión para acciones argentinas (BYMA) y CEDEARs. Corre 100% local: backend Python + frontend web.

## Arranque

```bash
./scripts/iniciar_backend.sh    # backend en http://localhost:8000
./scripts/iniciar_frontend.sh   # frontend en http://localhost:5173
```

O directamente doble click en **`Iniciar MOP.command`** (levanta ambos y abre el navegador). Los scripts instalan las dependencias solos la primera vez.

## Stack

| Capa | Tecnología |
|---|---|
| Backend | Python 3.9 · FastAPI · SQLite |
| Frontend | React 18 · Vite · TypeScript |
| Datos | yfinance |

## Estructura

```
backend/
├── app/
│   ├── main.py          ← app FastAPI
│   ├── routers/         ← endpoints HTTP
│   ├── servicios/       ← lógica de negocio
│   ├── repositorios/    ← acceso a la base de datos
│   └── esquemas/        ← modelos pydantic
└── tests/
frontend/
└── src/
    ├── api/             ← cliente HTTP (único lugar con fetch)
    ├── componentes/
    └── hooks/
scripts/                 ← arranque del backend y el frontend
```
