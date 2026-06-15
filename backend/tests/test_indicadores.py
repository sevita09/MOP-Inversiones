import statistics

from app.servicios.indicadores import calcular


def velas(cierres):
    return [
        {"ticker": "X", "temporalidad": "D", "ts": i, "apertura": c, "maximo": c,
         "minimo": c, "cierre": c, "volumen": 0.0}
        for i, c in enumerate(cierres)
    ]


def ema_manual(cierres, span):
    """EMA recursiva con adjust=False: ema[0]=cierre[0], luego α·c + (1−α)·ema."""
    alfa = 2 / (span + 1)
    valores = [float(cierres[0])]
    for c in cierres[1:]:
        valores.append(alfa * c + (1 - alfa) * valores[-1])
    return valores


# --- EMA ---


def test_ema_sigue_la_formula_recursiva():
    cierres = [10, 20, 30, 40, 35]
    salida = calcular("ema", velas(cierres), periodo=3)["ema"]
    esperado = [round(v, 6) for v in ema_manual(cierres, 3)]
    assert salida == esperado


def test_ema_de_serie_constante_es_la_constante():
    salida = calcular("ema", velas([50, 50, 50, 50]), periodo=10)["ema"]
    assert salida == [50.0, 50.0, 50.0, 50.0]


# --- MACD ---


def test_macd_es_diferencia_de_emas_con_su_senal():
    cierres = [10, 12, 11, 13, 15, 14, 16, 18, 17, 20]
    salida = calcular("macd", velas(cierres), rapida=2, lenta=4, senal=3)
    ema_rapida = ema_manual(cierres, 2)
    ema_lenta = ema_manual(cierres, 4)
    linea = [r - l for r, l in zip(ema_rapida, ema_lenta)]
    senal = ema_manual(linea, 3)
    assert salida["macd"] == [round(v, 6) for v in linea]
    assert salida["senal"] == [round(v, 6) for v in senal]
    assert salida["histograma"] == [round(li - se, 6) for li, se in zip(linea, senal)]


# --- z-score ---


def test_z_score_sigue_la_formula():
    cierres = [10, 12, 11, 13, 15, 14, 16, 18]
    salida = calcular("z_score", velas(cierres), ema_periodo=3, std_periodo=3)["z"]
    ema = ema_manual(cierres, 3)
    distancia = [c - e for c, e in zip(cierres, ema)]
    esperado = []
    for i in range(len(distancia)):
        if i < 2:  # ventana de 3 todavía incompleta → NaN
            esperado.append(None)
        else:
            ventana = distancia[i - 2 : i + 1]
            std = statistics.stdev(ventana)  # ddof=1, igual que pandas
            esperado.append(round(distancia[i] / std, 6) if std else None)
    assert salida == esperado


def test_z_score_positivo_si_el_precio_esta_sobre_la_ema():
    # serie alcista: el precio queda por encima de su EMA → z > 0
    z = calcular("z_score", velas(list(range(1, 30))), ema_periodo=5, std_periodo=5)["z"]
    assert z[-1] is not None and z[-1] > 0


# --- bandas (EMA central + σ) ---


def test_bandas_media_es_la_ema_del_periodo():
    cierres = [10, 12, 11, 13, 15, 14, 16]
    salida = calcular("bandas", velas(cierres), periodo=3)
    assert salida["media"] == [round(v, 6) for v in ema_manual(cierres, 3)]


def test_bandas_simetricas_alrededor_de_la_media():
    cierres = [10, 12, 11, 13, 15, 14, 16, 18, 17, 20]
    b = calcular("bandas", velas(cierres), periodo=3)
    for i, media in enumerate(b["media"]):
        if b["sup1"][i] is None:  # warmup sin σ
            continue
        sigma = b["sup1"][i] - media
        for k in (1, 2, 3):
            assert abs((b[f"sup{k}"][i] - media) - k * sigma) < 1e-5
            assert abs((media - b[f"inf{k}"][i]) - k * sigma) < 1e-5


def test_bandas_warmup_sin_sigma_es_none_pero_media_existe():
    cierres = [10, 12, 11]  # período 200 > longitud → σ rolling NaN, pero la EMA existe
    b = calcular("bandas", velas(cierres), periodo=200)
    assert all(v is not None for v in b["media"])
    assert b["sup1"] == [None, None, None]
    assert b["inf3"] == [None, None, None]


# --- RSI ---


def test_rsi_serie_solo_alcista_es_100():
    rsi = calcular("rsi", velas(list(range(1, 30))), periodo=14)["rsi"]
    assert rsi[-1] == 100.0  # sin pérdidas


def test_rsi_serie_solo_bajista_es_0():
    rsi = calcular("rsi", velas(list(range(30, 1, -1))), periodo=14)["rsi"]
    assert rsi[-1] == 0.0  # sin ganancias


def test_rsi_siempre_entre_0_y_100():
    cierres = [10, 12, 11, 13, 9, 14, 8, 15, 16, 12, 18, 11, 20, 19, 21, 17, 22, 25]
    rsi = calcular("rsi", velas(cierres), periodo=14)["rsi"]
    valores = [v for v in rsi if v is not None]
    assert valores and all(0 <= v <= 100 for v in valores)


def test_rsi_warmup_es_none():
    rsi = calcular("rsi", velas(list(range(1, 20))), periodo=14)["rsi"]
    assert rsi[0] is None  # no hay suficientes datos al inicio
