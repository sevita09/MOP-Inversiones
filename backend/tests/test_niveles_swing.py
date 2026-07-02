from app.servicios.niveles_swing import (
    VENTANA_TEMPORAL,
    agrupar_niveles,
    combinar,
    detectar_pivots,
    niveles_mensuales_recientes,
)

DIA = 86400


def vela(i, cierre, maximo=None, minimo=None, ts=None):
    return {
        "ts": ts if ts is not None else i * DIA,
        "apertura": cierre,
        "maximo": cierre if maximo is None else maximo,
        "minimo": cierre if minimo is None else minimo,
        "cierre": cierre,
        "volumen": 0.0,
        "es_faltante": 0,
    }


def serie(cierres):
    return [vela(i, c) for i, c in enumerate(cierres)]


# --- Detección de pivotes ---


def test_detecta_maximo_y_minimo_de_swing_sobre_el_cierre():
    cierres = [10, 11, 12, 20, 12, 11, 9, 5, 9, 11, 12]  # pico en 3, valle en 7
    pivots = detectar_pivots(serie(cierres), ventana=2)
    tipos = {(p["tipo"], p["precio"]) for p in pivots}
    assert ("resistencia", 20) in tipos
    assert ("soporte", 5) in tipos


def test_ignora_las_mechas_y_usa_solo_el_cierre():
    # Cierre constante pero una mecha altísima en el medio: no es un swing
    velas = [vela(i, 10, maximo=10) for i in range(7)]
    velas[3] = vela(3, 10, maximo=99)
    assert detectar_pivots(velas, ventana=2) == []


def test_ignora_las_velas_faltantes():
    velas = serie([10, 11, 12, 20, 12, 11, 10])
    velas[3]["es_faltante"] = 1  # el pico está sobre una vela de relleno
    pivots = detectar_pivots(velas, ventana=2)
    assert all(p["precio"] != 20 for p in pivots)


# --- Agrupamiento en niveles ---


def test_agrupa_pivotes_de_precio_cercano_y_cuenta_contactos():
    pivots = [
        {"ts": 0, "precio": 100.0, "tipo": "resistencia"},
        {"ts": 10 * DIA, "precio": 100.5, "tipo": "resistencia"},  # dentro de 1.5%
        {"ts": 20 * DIA, "precio": 200.0, "tipo": "soporte"},
    ]
    por_precio = {round(n["precio"]): n for n in agrupar_niveles(pivots)}
    assert por_precio[100]["contactos"] == 2
    assert por_precio[200]["contactos"] == 1


def test_separa_toques_al_mismo_precio_a_mas_de_un_ano():
    pivots = [
        {"ts": 0, "precio": 100.0, "tipo": "resistencia"},
        {"ts": VENTANA_TEMPORAL + 10 * DIA, "precio": 100.0, "tipo": "resistencia"},
    ]
    assert len(agrupar_niveles(pivots)) == 2


# --- Anclas mensuales recientes ---


def test_niveles_mensuales_recientes_son_fijos_y_del_ultimo_ano():
    cierres = []
    for k in range(12):
        cierres += [10, 20 + k]  # valles en 10, picos crecientes
    velas = [vela(i, c, ts=i * 30 * DIA) for i, c in enumerate(cierres)]
    niveles = niveles_mensuales_recientes(velas)
    corte = velas[-1]["ts"] - VENTANA_TEMPORAL
    assert niveles
    assert all(n["fijo"] for n in niveles)
    assert all(n["ultimo_ts"] >= corte for n in niveles)


# --- Combinación multitemporal ---


def test_combinar_diaria_superpone_las_anclas_mensuales_y_no_filtra_el_flag():
    diarias = serie([10 + (i % 5) for i in range(60)])
    mensuales = [
        vela(i, c, ts=i * 30 * DIA)
        for i, c in enumerate([10, 20, 10, 30, 10, 40, 10, 35, 10, 50, 10, 45])
    ]
    niveles = combinar({"D": diarias, "M": mensuales}, "D")
    assert "M" in {n["origen"] for n in niveles}  # anclas mensuales en la vista diaria
    assert all("fijo" not in n for n in niveles)  # el flag interno no llega al output
    assert all({"precio", "tipo", "contactos", "origen", "ultimo_ts"} <= n.keys() for n in niveles)
