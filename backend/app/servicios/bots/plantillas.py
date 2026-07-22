"""Las cuatro plantillas de estrategia de la metodología (ESTRATEGIAS_BOTS.md).

Diseñadas para el horizonte del usuario: 1-3 operaciones por mes por ticker,
tenencias de meses, reversión a la media por desvíos σ. La señal nace en
semanal/mensual (dónde está caro/barato); el diario solo aporta el gatillo
(cuándo entrar). Nunca "barato" sin "girando".

Todas ejecutan en D y con moneda USD por default: en pesos la EMA y las bandas
mezclan el negocio del papel con la devaluación (un salto del CCL dispara
z-scores falsos); la serie del ADR mide valor real.
"""
from __future__ import annotations

GATILLO_ESTOCASTICO_DIARIO = {
    "indicador": "estocastico",
    "serie": "k",
    "operador": "cruza_arriba",
    "objetivo": {"serie": "d"},
}

PLANTILLAS = [
    {
        "clave": "triple_confluencia",
        "nombre": "Triple confluencia mensual-semanal-diaria",
        "descripcion": "Reversión de máxima exigencia. Entra solo cuando el desvío mensual y el semanal coinciden en zona extrema (−2σ) y el estocástico diario confirma el giro al alza.",
        "horizonte": "1 a 3 señales por año por ticker · tenencia estimada de 3 a 9 meses",
        "temporalidad": "D",
        "moneda": "USD",
        "reglas": {
            "version": 1,
            "entrada": [
                {"indicador": "bandas", "serie": "z", "temporalidad": "M", "operador": "menor", "objetivo": -2},
                {"indicador": "bandas", "serie": "z", "temporalidad": "S", "operador": "menor", "objetivo": -2},
                GATILLO_ESTOCASTICO_DIARIO,
            ],
            "salida": [
                {"indicador": "bandas", "serie": "z", "temporalidad": "S", "operador": "mayor", "objetivo": 0}
            ],
            "filtros": [],
        },
    },
    {
        "clave": "reversion_semanal",
        "nombre": "Reversión semanal con filtro de tendencia",
        "descripcion": "Reversión de exigencia media sobre el desvío semanal (−1,5σ), con gatillo diario de cruce de la EMA 20 y un filtro mensual que descarta activos en tendencia bajista fuerte.",
        "horizonte": "1 a 2 señales por mes en tickers líquidos · tenencia estimada de 1 a 4 meses",
        "temporalidad": "D",
        "moneda": "USD",
        "reglas": {
            "version": 1,
            "entrada": [
                {"indicador": "bandas", "serie": "z", "temporalidad": "S", "operador": "menor", "objetivo": -1.5},
                {
                    "indicador": "ema",
                    "serie": "ema",
                    "operador": "cruza_arriba_precio",
                    "params": {"periodo": 20},
                },
            ],
            "salida": [
                {"indicador": "bandas", "serie": "z", "temporalidad": "S", "operador": "mayor", "objetivo": 0}
            ],
            "filtros": [
                {"indicador": "bandas", "serie": "z", "temporalidad": "M", "operador": "mayor", "objetivo": -3}
            ],
        },
    },
    {
        "clave": "sobreextension_percentil",
        "nombre": "Sobre-extensión por percentil",
        "descripcion": "Reversión calibrada por activo: mide la distancia a la media semanal en percentiles de la propia historia del papel, en lugar de desvíos σ fijos.",
        "horizonte": "Cadencia similar a la reversión semanal · referencia comparativa para el backtesting",
        "temporalidad": "D",
        "moneda": "USD",
        "reglas": {
            "version": 1,
            "entrada": [
                {
                    "indicador": "percentil_distancia",
                    "serie": "percentil",
                    "temporalidad": "S",
                    "operador": "menor",
                    "objetivo": 10,
                },
                GATILLO_ESTOCASTICO_DIARIO,
            ],
            "salida": [
                {
                    "indicador": "percentil_distancia",
                    "serie": "percentil",
                    "temporalidad": "S",
                    "operador": "mayor",
                    "objetivo": 50,
                }
            ],
            "filtros": [],
        },
    },
    {
        "clave": "cruce_de_emas",
        "nombre": "Cruce de medias móviles (referencia)",
        "descripcion": "Estrategia tendencial de control: cruce de las EMAs 10 y 30 en temporalidad semanal. Pensada como línea base para el backtesting, no para operar en vivo.",
        "horizonte": "Estrategia de control · referencia frente a las de reversión a la media",
        "temporalidad": "D",
        "moneda": "USD",
        "reglas": {
            "version": 1,
            "entrada": [
                {
                    "indicador": "ema",
                    "serie": "ema",
                    "temporalidad": "S",
                    "operador": "cruza_arriba",
                    "params": {"periodo": 10},
                    "objetivo": {"serie": "ema", "params": {"periodo": 30}},
                }
            ],
            "salida": [
                {
                    "indicador": "ema",
                    "serie": "ema",
                    "temporalidad": "S",
                    "operador": "cruza_abajo",
                    "params": {"periodo": 10},
                    "objetivo": {"serie": "ema", "params": {"periodo": 30}},
                }
            ],
            "filtros": [],
        },
    },
]


def listar_plantillas() -> list[dict]:
    return PLANTILLAS
