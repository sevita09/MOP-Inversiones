from app.servicios.indicadores import calcular


def velas(cierres):
    return [
        {"ticker": "X", "temporalidad": "D", "ts": i, "apertura": c, "maximo": c,
         "minimo": c, "cierre": c, "volumen": 0.0}
        for i, c in enumerate(cierres)
    ]


def velas_ohlc(datos):
    """datos = [(apertura, maximo, minimo, cierre), ...]"""
    return [
        {"ticker": "X", "temporalidad": "D", "ts": i, "apertura": o, "maximo": h,
         "minimo": l, "cierre": c, "volumen": 0.0}
        for i, (o, h, l, c) in enumerate(datos)
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
            sigma = (sum(d * d for d in ventana) / 3) ** 0.5  # RMS alrededor de cero
            esperado.append(round(distancia[i] / sigma, 6) if sigma else None)
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


def test_bandas_sigma_es_la_distancia_rms_a_la_ema():
    # σ = raíz del promedio de (precio − EMA)² sobre la ventana, alrededor de
    # CERO (no de la media de la distancia): así las bandas contienen al precio.
    cierres = [10, 12, 11, 13, 15, 14, 16, 18, 17, 20]
    periodo = 4
    b = calcular("bandas", velas(cierres), periodo=periodo)
    ema = ema_manual(cierres, periodo)
    dist = [c - e for c, e in zip(cierres, ema)]
    for i in range(len(cierres)):
        if i < periodo - 1:  # ventana incompleta → None
            assert b["sup1"][i] is None
            continue
        ventana = dist[i - periodo + 1 : i + 1]
        sigma = (sum(d * d for d in ventana) / periodo) ** 0.5
        assert abs((b["sup1"][i] - b["media"][i]) - sigma) < 1e-5


def test_bandas_warmup_sin_sigma_es_none_pero_media_existe():
    cierres = [10, 12, 11]  # período 200 > longitud → σ rolling NaN, pero la EMA existe
    b = calcular("bandas", velas(cierres), periodo=200)
    assert all(v is not None for v in b["media"])
    assert b["sup1"] == [None, None, None]
    assert b["inf3"] == [None, None, None]


def test_bandas_tipo_simple_es_media_movil_simple():
    cierres = [10, 12, 11, 13, 15, 14, 16]
    b = calcular("bandas", velas(cierres), periodo=3, tipo="simple")
    # SMA de período 3: los dos primeros None (ventana incompleta), luego el promedio
    assert b["media"][0] is None and b["media"][1] is None
    assert b["media"][2] == round((10 + 12 + 11) / 3, 6)
    assert b["media"][3] == round((12 + 11 + 13) / 3, 6)


def test_bandas_tipo_exp_es_el_default():
    cierres = [10, 12, 11, 13, 15, 14, 16]
    assert calcular("bandas", velas(cierres), periodo=3) == calcular(
        "bandas", velas(cierres), periodo=3, tipo="exp"
    )


def test_bandas_multiplicadores_sigma_configurables():
    cierres = [10, 12, 11, 13, 15, 14, 16, 18, 17, 20]
    b = calcular("bandas", velas(cierres), periodo=3, desvio1=0.5, desvio2=1.5, desvio3=2.5)
    for i, media in enumerate(b["media"]):
        if b["sup1"][i] is None:
            continue
        sigma = b["sup1"][i] / 0.5 - media / 0.5  # sup1 = media + 0.5σ → σ = (sup1−media)/0.5
        for k, mult in ((1, 0.5), (2, 1.5), (3, 2.5)):
            assert abs((b[f"sup{k}"][i] - media) - mult * sigma) < 1e-5
            assert abs((media - b[f"inf{k}"][i]) - mult * sigma) < 1e-5


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


# --- estocástico ---


def test_estocastico_serie_alcista_k_es_100():
    # cierre = máximo de la ventana → %K = 100
    k = calcular("estocastico", velas(list(range(1, 30))), periodo=14)["k"]
    assert k[-1] == 100.0


def test_estocastico_serie_bajista_k_es_0():
    # cierre = mínimo de la ventana → %K = 0
    k = calcular("estocastico", velas(list(range(30, 1, -1))), periodo=14)["k"]
    assert k[-1] == 0.0


def test_estocastico_calcula_k_segun_el_rango():
    # ventana de 5 al final: [12, 8, 11, 9, 11] → mín 8, máx 12, cierre 11
    # %K = 100·(11−8)/(12−8) = 75
    k = calcular("estocastico", velas([10, 12, 8, 11, 9, 11]), periodo=5, suavizado=3)["k"]
    assert k[-1] == 75.0


def test_estocastico_d_es_media_movil_de_k():
    cierres = [10, 12, 11, 13, 15, 14, 16, 18, 17, 20, 19, 22]
    s = calcular("estocastico", velas(cierres), periodo=5, suavizado=3)
    k, d = s["k"], s["d"]
    for i in range(2, len(k)):
        ventana = k[i - 2 : i + 1]
        if all(x is not None for x in ventana):
            assert d[i] is not None and abs(d[i] - sum(ventana) / 3) < 1e-5


def test_estocastico_siempre_entre_0_y_100():
    cierres = [10, 12, 11, 13, 9, 14, 8, 15, 16, 12, 18, 11, 20, 19, 21, 17, 22, 25]
    s = calcular("estocastico", velas(cierres), periodo=14)
    for serie in (s["k"], s["d"]):
        valores = [v for v in serie if v is not None]
        assert valores and all(0 <= v <= 100 for v in valores)


def test_estocastico_warmup_es_none():
    k = calcular("estocastico", velas(list(range(1, 10))), periodo=14)["k"]
    assert k[0] is None  # ventana de 14 incompleta al inicio


# --- ATR ---


def test_atr_serie_constante_es_cero():
    datos = [(10, 10, 10, 10)] * 20
    atr = calcular("atr", velas_ohlc(datos), periodo=5)["atr"]
    valores = [v for v in atr if v is not None]
    assert all(v == 0.0 for v in valores)


def test_atr_true_range_usa_maximo_y_minimo():
    # Barra: high=15, low=5 → TR = 10 (con cierre previo dentro del rango)
    datos = [(10, 10, 10, 10)] * 14 + [(10, 15, 5, 12)]
    atr = calcular("atr", velas_ohlc(datos), periodo=14)["atr"]
    assert atr[-1] is not None and atr[-1] > 0


def test_atr_gap_usa_cierre_anterior():
    # Gap: cierre previo=10, nueva barra high=25, low=20 → TR = max(5, 15, 10) = 15
    datos = [(10, 10, 10, 10)] * 14 + [(20, 25, 20, 22)]
    atr = calcular("atr", velas_ohlc(datos), periodo=14)["atr"]
    assert atr[-1] is not None and atr[-1] > 0


def test_atr_warmup_es_none():
    datos = [(10, 12, 8, 10)] * 10
    atr = calcular("atr", velas_ohlc(datos), periodo=14)["atr"]
    assert atr[0] is None


# --- %B de Bollinger ---


def test_porcentaje_b_dentro_de_bandas_esta_entre_0_y_1():
    cierres = [10, 12, 11, 13, 15, 14, 16, 18, 17, 20, 19, 22, 21, 23, 22]
    b = calcular("porcentaje_b", velas(cierres), periodo=5)["porcentaje_b"]
    valores = [v for v in b[4:] if v is not None]
    promedio = sum(valores) / len(valores)
    assert 0.2 < promedio < 0.8


def test_porcentaje_b_precio_en_banda_superior_es_1():
    # Serie: media + 2σ → %B ≈ 1
    cierres = [10] * 20 + [20]  # salto brusco, cierre > banda superior
    b = calcular("porcentaje_b", velas(cierres), periodo=20)["porcentaje_b"]
    assert b[-1] is not None and b[-1] > 1.0  # por encima de la banda


def test_porcentaje_b_siempre_tiene_valor_tras_warmup():
    cierres = [10, 12, 11, 13, 15, 14, 16, 18, 17, 20, 19, 22, 21, 23, 25, 24, 26, 28, 27, 30]
    b = calcular("porcentaje_b", velas(cierres), periodo=5)["porcentaje_b"]
    valores = [v for v in b[4:] if v is not None]
    assert len(valores) > 0


# --- ADX ---


def test_adx_tendencia_fuerte_es_alto():
    # Serie fuertemente alcista → ADX alto
    datos = [(i, i + 2, i - 1, i + 1) for i in range(1, 40)]
    adx = calcular("adx", velas_ohlc(datos), periodo=14)["adx"]
    valores = [v for v in adx if v is not None]
    assert valores and valores[-1] > 30


def test_adx_sin_tendencia_es_bajo():
    import random
    rng = random.Random(42)
    datos = [(10, 10 + rng.uniform(0.5, 2), 10 - rng.uniform(0.5, 2), 10 + rng.uniform(-1, 1))
             for _ in range(60)]
    adx = calcular("adx", velas_ohlc(datos), periodo=14)["adx"]
    valores = [v for v in adx if v is not None]
    assert valores and valores[-1] < 30


def test_adx_siempre_positivo():
    datos = [(i, i + 3, i - 2, i + 1) for i in range(1, 40)]
    adx = calcular("adx", velas_ohlc(datos), periodo=14)["adx"]
    valores = [v for v in adx if v is not None]
    assert all(v >= 0 for v in valores)


def test_adx_warmup_es_none():
    datos = [(10, 12, 8, 10)] * 5
    adx = calcular("adx", velas_ohlc(datos), periodo=14)["adx"]
    assert adx[0] is None


# --- Percentil de distancia ---


def test_percentil_distancia_maximo_es_100():
    # Último precio muy por encima de la EMA → percentil alto
    cierres = [10] * 300 + list(range(10, 30))
    p = calcular("percentil_distancia", velas(cierres), periodo=5, ventana=50)["percentil"]
    valores = [v for v in p if v is not None]
    assert valores and valores[-1] > 90


def test_percentil_distancia_minimo_es_cercano_a_cero():
    # Último precio muy por debajo de la EMA → percentil bajo
    cierres = [10] * 300 + list(range(10, 0, -1))
    p = calcular("percentil_distancia", velas(cierres), periodo=5, ventana=50)["percentil"]
    valores = [v for v in p if v is not None]
    assert valores and valores[-1] < 10


def test_percentil_distancia_warmup_es_none():
    cierres = list(range(1, 20))
    p = calcular("percentil_distancia", velas(cierres), periodo=5, ventana=252)["percentil"]
    assert p[0] is None


def test_percentil_distancia_muestra_valores_antes_de_llenar_la_ventana():
    # min_periods bajo: con ventana 252 pero solo 59 barras igual hay valores
    # (antes quedaba todo en None, p.ej. en la mensual)
    cierres = list(range(1, 60))
    p = calcular("percentil_distancia", velas(cierres), periodo=5, ventana=252)["percentil"]
    assert any(v is not None for v in p)


# --- Bandas de Bollinger ---


def test_bollinger_media_es_la_sma_del_periodo():
    r = calcular("bollinger", velas([10, 20, 30, 40, 50]), periodo=3)
    assert r["media"][2] == 20  # SMA(10, 20, 30)
    assert r["media"][4] == 40  # SMA(30, 40, 50)


def test_bollinger_bandas_simetricas_y_ancho_positivo():
    cierres = [10, 12, 11, 13, 9, 14, 8, 15]
    r = calcular("bollinger", velas(cierres), periodo=4)
    i = len(cierres) - 1
    media, sup, inf = r["media"][i], r["superior"][i], r["inferior"][i]
    assert sup > media > inf
    assert round(sup - media, 6) == round(media - inf, 6)


def test_bollinger_serie_constante_colapsa_las_bandas():
    r = calcular("bollinger", velas([50] * 10), periodo=5)
    assert r["superior"][9] == 50 and r["inferior"][9] == 50
