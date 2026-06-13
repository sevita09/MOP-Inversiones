# Flujo de datos y sincronización

## Temporalidades

| Código | Significado | Historia inicial | Vigencia (re-sync) |
|---|---|---|---|
| `H` | Hora | 2 años (límite de yfinance gratuito) | 1 hora |
| `D` | Día | 10 años | 1 día |
| `S` | Semana | 10 años | 7 días |
| `M` | Mes | 10 años | 30 días |

La nomenclatura `H/D/S/M` se usa en toda la app (base, API, UI). El mapeo a los
códigos de yfinance (`1h/1d/1wk/1mo`) vive en `config.INTERVALO_YFINANCE` y se
usa únicamente al descargar.

## Símbolos de Yahoo Finance

- Tickers BYMA → sufijo `.BA` (`GGAL` → `GGAL.BA`).
- `GGALD` (ADR de GGAL en NYSE, infraestructura para el CCL) → `GGAL`.
- El resto (CEDEARs/NYSE) → sin cambios.

## Flujo de sincronización

```
arranque de la app (lifespan)          POST /api/sync
        │                                   │
        └────────────┬──────────────────────┘
                     ▼
        sincronizar_en_background()
            │  threading.Lock no bloqueante:
            │  si ya hay un sync corriendo → "ya_en_curso"
            ▼
        sincronizar_todo()  (thread propio, conexión propia)
            │
            │  por cada ticker × temporalidad:
            ▼
        ¿está vencido?  ──no──▶ no descarga nada
            │ sí (registro_sync más viejo que la vigencia, o nunca sincronizado)
            ▼
        descargar_velas()
            │  · primera vez: toda la historia configurada (period)
            │  · siguientes: delta desde la última vela guardada inclusive
            │    (la vela en curso se refresca; el upsert la pisa)
            │  · filtra velas con precios en cero o NaN antes de insertar
            ▼
        guardar_velas()  (INSERT OR REPLACE)
            ▼
        registrar_sync()  (momento ISO UTC en registro_sync)
            │
            │  al terminar todas las temporalidades del ticker:
            ▼
        refrescar_velas_en_curso()
            ·  si D quedó más actualizada que S o M, la vela S/M en curso
               toma el último cierre diario y recalcula extremos y volumen
               con las diarias de su período (sin contaminar con el siguiente)
            ·  el próximo sync real de S/M pisa la vela con el dato de yfinance
```

El resumen del último sync (velas guardadas, pares sincronizados, velas
refrescadas, errores por ticker) queda disponible en `GET /api/sync`.

## Endpoints

| Método | Ruta | Descripción |
|---|---|---|
| GET | `/api/tickers` | Universo agrupado: panel líder, panel general, CEDEARs |
| GET | `/api/velas?ticker=GGAL&temporalidad=D&desde=&hasta=` | Velas de la base (ts unix, orden ascendente) |
| POST | `/api/sync` | Lanza el sync en background (`iniciado` / `ya_en_curso`) |
| GET | `/api/sync` | Estado: `en_curso` + `ultimo_resumen` |

## Reglas

- La base **apendea**: la descarga profunda es solo la primera vez; lo viejo
  nunca se borra (la ventana no es móvil).
- Un error en un ticker no frena el sync del resto: queda en `errores` del resumen.
- Los tests **nunca llaman a yfinance**: datos sintéticos con seed fija y mocks.
