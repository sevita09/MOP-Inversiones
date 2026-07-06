<p align="center">
  <img src="frontend/public/sv-logo.png" width="120" alt="MOP Inversiones">
</p>

# MOP - Inversiones

Plataforma personal de análisis e inversión para acciones argentinas (BYMA) y CEDEARs. Corre 100% local: backend Python + frontend web.

## Instalar (app de escritorio)

1. Descargar el `.dmg` de la [última release](https://github.com/sevita09/MOP-Inversiones/releases).
2. Abrirlo y arrastrar **MOP - Inversiones** a **Aplicaciones**.
3. Primera vez: clic derecho → **Abrir** (la app usa firma ad-hoc, sin notarizar).

Los datos (base, respaldos, logos) viven en `~/Library/Application Support/MOP` — actualizar la app nunca los toca.

## Actualizar

La app chequea al arrancar si hay una versión nueva en GitHub y muestra el aviso en la barra superior. Descargar el `.dmg` nuevo y pisar el `.app` en Aplicaciones: listo.

Para publicar una versión (desarrollo): cerrar la versión con su tag `vX.Y.Z` pusheado y correr

```bash
./scripts/crear_dmg.sh          # build frontend + PyInstaller + .dmg en backend/dist/
./scripts/publicar_release.sh   # release en GitHub con el .dmg adjunto
```

## Modo desarrollo (web)

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
scripts/                 ← arranque en desarrollo + empaquetado (.dmg y release)
```
