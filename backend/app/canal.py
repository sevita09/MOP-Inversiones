"""Canal de la app: "prod" (la instalada) o "dev" (la de pruebas).

El script scripts/crear_app_dev.sh lo pone en "dev" durante el build de la app
de desarrollo y lo restaura. El canal dev usa otro puerto, otra carpeta de
datos y no ofrece auto-actualización.
"""

CANAL = "prod"
