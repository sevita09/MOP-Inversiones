"""Detección de niveles de soporte/resistencia a partir de swings.

Un pivote (swing) es un máximo o mínimo local: el `maximo`/`minimo` de una vela
que supera a las N velas de cada lado. Los pivotes de precio cercano se agrupan
en un mismo NIVEL y se cuentan los "contactos" (cuántos swings lo tocaron): más
contactos = nivel más fuerte.

Sobre el chart de una temporalidad se muestran sus niveles propios (los recientes
o los fuertes) y, superpuestos, los niveles FUERTES de las temporalidades
superiores (semanal/mensual sobre el diario). Cada nivel viaja etiquetado con su
temporalidad de `origen`.
"""
from __future__ import annotations

SEGUNDOS_POR_DIA = 86400

# Velas a cada lado para confirmar un swing, POR temporalidad (la mensual tiene
# pocas barras: una ventana grande la dejaría sin pivots).
VENTANA_PIVOTE = {"H": 6, "D": 6, "S": 4, "M": 2}
VENTANA_PIVOTE_DEFECTO = 5
TOLERANCIA_NIVEL = 0.015                    # pivotes dentro de ±1.5% = mismo nivel de precio
VENTANA_TEMPORAL = 365 * SEGUNDOS_POR_DIA   # toques a >1 año entre sí = niveles distintos
CONTACTOS_FUERTE = 3        # nivel "fuerte": se superpone en temporalidades inferiores
CONTACTOS_MACRO = 2         # mínimo para mostrar un nivel propio en semanal/mensual
RECIENTE_DIAS = 90          # "cercano": ~3 meses, para el filtro de la diaria/horaria
BANDA_PRECIO = 0.40         # solo niveles dentro de ±40% del precio actual (el resto es ruido)
MAX_NIVELES = 12            # tope para no saturar el chart
CANT_MENSUAL_RECIENTE = 2   # últimos máximos y mínimos mensuales que se muestran siempre
VENTANA_MENSUAL_RECIENTE = 1  # ventana chica para detectar esos picos/valles recientes

# Temporalidades superiores que se superponen (solo niveles fuertes) sobre cada vista
SUPERIORES = {"H": ["D"], "D": ["S", "M"], "S": ["M"], "M": []}

# Jerarquía para el desempate: si dos niveles de distinto origen se solapan,
# gana el de temporalidad más alta (macro manda sobre micro).
_JERARQUIA = {"M": 3, "S": 2, "D": 1, "H": 0}


def _ventana(temporalidad: str) -> int:
    return VENTANA_PIVOTE.get(temporalidad, VENTANA_PIVOTE_DEFECTO)


def detectar_pivots(velas: list[dict], ventana: int = VENTANA_PIVOTE_DEFECTO) -> list[dict]:
    """Devuelve los swings sobre el precio de CIERRE: máximos y mínimos locales.

    Se usa el cierre (no el máximo/mínimo de la vela) porque las mechas suelen ser
    ruido; los niveles que importan son los de cierre. Ignora las velas
    faltantes/interpoladas (`es_faltante`) para no inventar pivotes sobre relleno.
    """
    reales = [v for v in velas if not v.get("es_faltante")]
    pivots: list[dict] = []
    n = len(reales)
    for i in range(ventana, n - ventana):
        cierre = reales[i]["cierre"]
        vecinos = [j for j in range(i - ventana, i + ventana + 1) if j != i]
        if all(reales[j]["cierre"] <= cierre for j in vecinos) and any(
            reales[j]["cierre"] < cierre for j in vecinos
        ):
            pivots.append({"ts": reales[i]["ts"], "precio": cierre, "tipo": "resistencia"})
        if all(reales[j]["cierre"] >= cierre for j in vecinos) and any(
            reales[j]["cierre"] > cierre for j in vecinos
        ):
            pivots.append({"ts": reales[i]["ts"], "precio": cierre, "tipo": "soporte"})
    return pivots


def agrupar_niveles(
    pivots: list[dict],
    tolerancia: float = TOLERANCIA_NIVEL,
    ventana_temporal: int = VENTANA_TEMPORAL,
) -> list[dict]:
    """Agrupa pivotes en niveles con conteo de contactos.

    Primero por precio cercano (±`tolerancia`) y, dentro de cada banda de precio,
    por cercanía temporal: dos toques a más de `ventana_temporal` entre sí forman
    niveles distintos (un soporte que quedó un año sin tocarse y vuelve es otro
    nivel, no suma contacto al viejo).
    """
    if not pivots:
        return []
    # 1) Bandas por precio
    ordenados = sorted(pivots, key=lambda p: p["precio"])
    bandas: list[list[dict]] = [[ordenados[0]]]
    for p in ordenados[1:]:
        base = bandas[-1][0]["precio"]  # el más bajo de la banda (viene ordenado)
        if base > 0 and abs(p["precio"] - base) / base <= tolerancia:
            bandas[-1].append(p)
        else:
            bandas.append([p])

    # 2) Dentro de cada banda, cortar por saltos temporales mayores a un año
    niveles: list[dict] = []
    for banda in bandas:
        por_tiempo = sorted(banda, key=lambda p: p["ts"])
        grupo = [por_tiempo[0]]
        for p in por_tiempo[1:]:
            if p["ts"] - grupo[-1]["ts"] <= ventana_temporal:
                grupo.append(p)
            else:
                niveles.append(_nivel_de_grupo(grupo))
                grupo = [p]
        niveles.append(_nivel_de_grupo(grupo))
    return niveles


def _nivel_de_grupo(grupo: list[dict]) -> dict:
    precios = [p["precio"] for p in grupo]
    resistencias = sum(1 for p in grupo if p["tipo"] == "resistencia")
    soportes = len(grupo) - resistencias
    if resistencias > soportes:
        tipo = "resistencia"
    elif soportes > resistencias:
        tipo = "soporte"
    else:
        tipo = "mixto"
    return {
        "precio": round(sum(precios) / len(precios), 4),
        "contactos": len(grupo),
        "tipo": tipo,
        "ultimo_ts": max(p["ts"] for p in grupo),
    }


def niveles_propios(velas: list[dict], temporalidad: str) -> list[dict]:
    """Niveles de la propia temporalidad, ya filtrados según la vista.

    - Diaria/horaria: solo los recientes (~3 meses) o los fuertes (evita saturar).
    - Semanal/mensual: los macro significativos (al menos 2 contactos), sin recorte
      temporal.
    """
    niveles = agrupar_niveles(detectar_pivots(velas, _ventana(temporalidad)))
    if not niveles:
        return []
    if temporalidad in ("D", "H"):
        reales = [v for v in velas if not v.get("es_faltante")]
        if not reales:
            return []
        corte = max(v["ts"] for v in reales) - RECIENTE_DIAS * SEGUNDOS_POR_DIA
        return [
            n for n in niveles
            if n["ultimo_ts"] >= corte or n["contactos"] >= CONTACTOS_FUERTE
        ]
    # Semanal: solo niveles significativos (≥2 contactos). Mensual: hay pocas
    # barras, un swing único ya es un nivel válido.
    umbral = 1 if temporalidad == "M" else CONTACTOS_MACRO
    return [n for n in niveles if n["contactos"] >= umbral]


def niveles_mensuales_recientes(velas_m: list[dict]) -> list[dict]:
    """Los últimos máximos y mínimos de swing MENSUAL del último año.

    Son referencia macro: se muestran SIEMPRE (marcados `fijo`), aunque tengan un
    solo toque y sin importar el filtro de contactos ni el de cercanía.
    """
    pivots = detectar_pivots(velas_m, VENTANA_MENSUAL_RECIENTE)
    reales = [v for v in velas_m if not v.get("es_faltante")]
    if not pivots or not reales:
        return []
    corte = reales[-1]["ts"] - VENTANA_TEMPORAL
    recientes = [p for p in pivots if p["ts"] >= corte]

    def ultimos(tipo: str) -> list[dict]:
        del_tipo = sorted(
            (p for p in recientes if p["tipo"] == tipo),
            key=lambda p: p["ts"],
            reverse=True,
        )
        return del_tipo[:CANT_MENSUAL_RECIENTE]

    elegidos = ultimos("resistencia") + ultimos("soporte")
    return [{**n, "fijo": True} for n in agrupar_niveles(elegidos)]


def combinar(velas_por_temporalidad: dict[str, list[dict]], temporalidad: str) -> list[dict]:
    """Niveles propios + niveles FUERTES de las temporalidades superiores + los
    últimos máximos/mínimos mensuales del último año (referencia macro fija).

    `velas_por_temporalidad`: dict {temporalidad: velas}; debe traer la vista y las
    superiores que correspondan (ver SUPERIORES). Cada nivel devuelto lleva `origen`.
    """
    candidatos: list[dict] = []
    for n in niveles_propios(velas_por_temporalidad.get(temporalidad, []), temporalidad):
        candidatos.append({**n, "origen": temporalidad})
    for sup in SUPERIORES.get(temporalidad, []):
        for n in agrupar_niveles(detectar_pivots(velas_por_temporalidad.get(sup, []), _ventana(sup))):
            if n["contactos"] >= CONTACTOS_FUERTE:
                candidatos.append({**n, "origen": sup})
    # Los máximos/mínimos mensuales recientes se muestran siempre (salvo en la
    # propia vista mensual, donde ya salen como niveles propios)
    if temporalidad != "M" and velas_por_temporalidad.get("M"):
        for n in niveles_mensuales_recientes(velas_por_temporalidad["M"]):
            candidatos.append({**n, "origen": "M"})
    return _seleccionar(candidatos, _ultimo_cierre(velas_por_temporalidad.get(temporalidad, [])))


def _ultimo_cierre(velas: list[dict]) -> float | None:
    reales = [v for v in velas if not v.get("es_faltante")]
    return reales[-1]["cierre"] if reales else None


def _seleccionar(niveles: list[dict], precio_actual: float | None) -> list[dict]:
    """Descarta solapados (dedup), recorta el resto a los cercanos al precio actual
    y deja los más relevantes (jerarquía + contactos), con un tope. Los niveles
    `fijo` (máximos/mínimos mensuales recientes) se muestran siempre: no los recorta
    ni el filtro de cercanía ni el tope."""
    elegidos = _deduplicar(niveles)
    fijos = [n for n in elegidos if n.get("fijo")]
    resto = [n for n in elegidos if not n.get("fijo")]
    if precio_actual and precio_actual > 0:
        resto = [
            n for n in resto
            if abs(n["precio"] - precio_actual) / precio_actual <= BANDA_PRECIO
        ]
    resto.sort(
        key=lambda n: (_JERARQUIA.get(n["origen"], 0), n["contactos"]),
        reverse=True,
    )
    combinados = fijos + resto[: max(0, MAX_NIVELES - len(fijos))]
    combinados.sort(key=lambda n: n["precio"])
    return [{k: v for k, v in n.items() if k != "fijo"} for n in combinados]


def _deduplicar(niveles: list[dict], tolerancia: float = TOLERANCIA_NIVEL) -> list[dict]:
    """Si dos niveles se solapan, se queda el fijo o el de mayor jerarquía y más
    contactos."""
    orden = sorted(
        niveles,
        key=lambda n: (n.get("fijo", False), _JERARQUIA.get(n["origen"], 0), n["contactos"]),
        reverse=True,
    )
    elegidos: list[dict] = []
    for n in orden:
        base = n["precio"]
        if any(base > 0 and abs(base - e["precio"]) / base <= tolerancia for e in elegidos):
            continue
        elegidos.append(n)
    return sorted(elegidos, key=lambda n: n["precio"])
