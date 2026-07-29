"""Curva diaria de valor, flujos de capital y TWR contra los benchmarks."""
from datetime import datetime, timezone

from app.repositorios import splits as repo_splits
from app.repositorios import transacciones as repo
from app.repositorios.tasas_dolar import guardar_tasas
from app.servicios.inflacion import guardar_inflacion
from app.repositorios.velas import guardar_velas
from app.servicios.cartera.benchmarks import comparacion, curva_base_100, retornos_diarios, twr
from app.servicios.cartera.curva import serie_valor


def _ts(fecha: str) -> int:
    return int(datetime.strptime(fecha, "%Y-%m-%d").replace(tzinfo=timezone.utc).timestamp())


def _velas(conexion, ticker, precios_por_fecha):
    guardar_velas(
        conexion,
        [
            {"ticker": ticker, "temporalidad": "D", "ts": _ts(fecha), "apertura": precio,
             "maximo": precio, "minimo": precio, "cierre": precio, "volumen": 1000,
             "es_faltante": 0}
            for fecha, precio in precios_por_fecha.items()
        ],
    )


def _operacion(conexion, tipo, cantidad, precio, fecha, ticker="GGAL", comision=0):
    return repo.crear(conexion, ticker, tipo, fecha, cantidad, precio, comision)


def _tasas(conexion, tipo, *pares):
    guardar_tasas(
        conexion, [{"fecha": f, "tipo": tipo, "valor": v} for f, v in pares]
    )


RUEDAS = ["2026-01-05", "2026-01-06", "2026-01-07"]


# --- serie de valor ---


def test_sin_operaciones_no_hay_curva(conexion):
    assert serie_valor(conexion) == []


def test_el_valor_es_la_tenencia_por_el_cierre(conexion):
    _velas(conexion, "GGAL", {"2026-01-05": 1000, "2026-01-06": 1100, "2026-01-07": 900})
    _operacion(conexion, "compra", 100, 1000, "2026-01-05")

    serie = serie_valor(conexion)
    assert [p["fecha"] for p in serie] == RUEDAS
    assert [p["valor"] for p in serie] == [100_000, 110_000, 90_000]


def test_la_compra_es_un_flujo_que_entra_con_sus_gastos(conexion):
    _velas(conexion, "GGAL", {"2026-01-05": 1000, "2026-01-06": 1000})
    _operacion(conexion, "compra", 100, 1000, "2026-01-05", comision=500)

    serie = serie_valor(conexion)
    assert serie[0]["flujo"] == 100_500  # lo que salió del bolsillo
    assert serie[1]["flujo"] == 0


def test_la_venta_es_un_flujo_que_sale_neto_de_gastos(conexion):
    _velas(conexion, "GGAL", {"2026-01-05": 1000, "2026-01-06": 1000, "2026-01-07": 1000})
    _operacion(conexion, "compra", 100, 1000, "2026-01-05")
    _operacion(conexion, "venta", 100, 1000, "2026-01-06", comision=700)

    serie = serie_valor(conexion)
    assert serie[1]["flujo"] == -99_300
    assert serie[2]["valor"] == 0  # ya no queda nada en cartera


def test_una_compra_en_dia_sin_rueda_se_imputa_a_la_siguiente(conexion):
    """Una operación cargada un sábado no puede perder su flujo de capital."""
    _velas(conexion, "GGAL", {"2026-01-05": 1000, "2026-01-06": 1000})
    _operacion(conexion, "compra", 100, 1000, "2026-01-03")  # sábado, sin rueda

    serie = serie_valor(conexion)
    assert serie[0]["fecha"] == "2026-01-05"
    assert serie[0]["flujo"] == 100_000
    assert serie[0]["valor"] == 100_000


def test_el_split_no_mueve_el_valor(conexion):
    """Al doble de papeles a mitad de precio, la cartera vale lo mismo."""
    _velas(conexion, "GGAL", {"2026-01-05": 1000, "2026-01-06": 500})
    _operacion(conexion, "compra", 100, 1000, "2026-01-05")
    repo_splits.crear(conexion, "GGAL", "2026-01-06", 2)

    serie = serie_valor(conexion)
    assert [p["valor"] for p in serie] == [100_000, 100_000]


def test_en_usd_cada_rueda_usa_su_mep(conexion):
    _velas(conexion, "GGAL", {"2026-01-05": 1000, "2026-01-06": 1000})
    guardar_tasas(
        conexion,
        [
            {"fecha": "2026-01-05", "tipo": "MEP", "valor": 1000},
            {"fecha": "2026-01-06", "tipo": "MEP", "valor": 2000},
        ],
    )
    _operacion(conexion, "compra", 100, 1000, "2026-01-05")

    serie = serie_valor(conexion, moneda="USD")
    # El precio en pesos no se movió, pero el dólar se duplicó: vale la mitad
    assert [p["valor"] for p in serie] == [100.0, 50.0]
    assert serie[0]["flujo"] == 100.0


# --- TWR ---


def test_sin_flujos_el_twr_es_la_variacion_del_precio(conexion):
    _velas(conexion, "GGAL", {"2026-01-05": 1000, "2026-01-06": 1100, "2026-01-07": 1210})
    _operacion(conexion, "compra", 100, 1000, "2026-01-05")

    assert twr(serie_valor(conexion)) == 21.0  # 1,1 × 1,1 − 1


def test_el_aporte_no_infla_el_twr(conexion):
    """Duplicar la posición sin que el precio se mueva no es rendimiento."""
    _velas(conexion, "GGAL", {"2026-01-05": 1000, "2026-01-06": 1000, "2026-01-07": 1100})
    _operacion(conexion, "compra", 100, 1000, "2026-01-05")
    _operacion(conexion, "compra", 100, 1000, "2026-01-06")

    serie = serie_valor(conexion)
    assert [p["valor"] for p in serie] == [100_000, 200_000, 220_000]
    # El retorno simple sobre lo aportado diría otra cosa; el TWR ve solo el 10%
    assert round(retornos_diarios(serie)[0], 6) == 0.0
    assert twr(serie) == 10.0


def test_el_retiro_no_hunde_el_twr(conexion):
    _velas(conexion, "GGAL", {"2026-01-05": 1000, "2026-01-06": 1000, "2026-01-07": 1100})
    _operacion(conexion, "compra", 200, 1000, "2026-01-05")
    _operacion(conexion, "venta", 100, 1000, "2026-01-06")

    serie = serie_valor(conexion)
    assert [p["valor"] for p in serie] == [200_000, 100_000, 110_000]
    assert twr(serie) == 10.0


def test_la_curva_base_100_arranca_en_100(conexion):
    _velas(conexion, "GGAL", {"2026-01-05": 1000, "2026-01-06": 1100})
    _operacion(conexion, "compra", 100, 1000, "2026-01-05")
    assert curva_base_100(serie_valor(conexion)) == [100.0, 110.0]


# --- benchmarks ---


def test_compara_contra_el_dolar_y_el_merval(conexion):
    """La cartera sube 10%, el dólar 5% y el MERVAL 20%: le gana a uno solo."""
    _velas(conexion, "GGAL", {"2026-01-05": 1000, "2026-01-06": 1100})
    _velas(conexion, "MERVAL", {"2026-01-05": 2_000_000, "2026-01-06": 2_400_000})
    _tasas(conexion, "CCL", ("2026-01-05", 1000), ("2026-01-06", 1050))
    _operacion(conexion, "compra", 100, 1000, "2026-01-05")

    resultado = comparacion(conexion)
    assert resultado["cartera"] == [100.0, 110.0]
    assert resultado["benchmarks"]["dolar"] == [100.0, 105.0]
    assert resultado["benchmarks"]["mercado"] == [100.0, 120.0]

    totales = resultado["totales"]
    assert totales["twr_pct"] == 10.0
    assert totales["contra"]["dolar"] == 5.0  # +5 puntos contra el dólar
    assert totales["contra_mercado"] == -10.0  # −10 contra el mercado
    assert totales["variaciones"]["mercado"] == 20.0


def test_un_benchmark_en_dolares_se_pasa_a_pesos(conexion):
    """El S&P en pesos es lo que hubiera valido tenerlo acá: precio × dólar."""
    _velas(conexion, "GGAL", {"2026-01-05": 1000, "2026-01-06": 1000})
    _velas(conexion, "SPY", {"2026-01-05": 500, "2026-01-06": 550})
    _tasas(conexion, "MEP", ("2026-01-05", 1000), ("2026-01-06", 2000))
    _operacion(conexion, "compra", 100, 1000, "2026-01-05")

    # El S&P subió 10% en dólares y el dólar se duplicó: en pesos hizo +120%
    assert comparacion(conexion)["benchmarks"]["spy"] == [100.0, 220.0]
    # En dólares es su propia variación, sin tocar
    assert comparacion(conexion, moneda="USD")["benchmarks"]["spy"] == [100.0, 110.0]


def test_berkshire_solo_aparece_en_dolares(conexion):
    """En pesos su lugar lo ocupa la inflación."""
    _velas(conexion, "GGAL", {"2026-01-05": 1000, "2026-01-06": 1100})
    _velas(conexion, "BRKB", {"2026-01-05": 400, "2026-01-06": 420})
    _tasas(conexion, "MEP", ("2026-01-05", 1000), ("2026-01-06", 1000))
    _operacion(conexion, "compra", 100, 1000, "2026-01-05")

    assert "brkb" not in comparacion(conexion)["benchmarks"]
    assert comparacion(conexion, moneda="USD")["benchmarks"]["brkb"] == [100.0, 105.0]


def test_los_totales_separan_lo_aportado_de_la_ganancia(conexion):
    _velas(conexion, "GGAL", {"2026-01-05": 1000, "2026-01-06": 1200})
    _operacion(conexion, "compra", 100, 1000, "2026-01-05", comision=500)

    totales = comparacion(conexion)["totales"]
    assert totales["aportado_neto"] == 100_500
    assert totales["valor_actual"] == 120_000
    assert totales["ganancia"] == 19_500  # 120.000 − 100.500 puestos


def test_la_ganancia_de_un_periodo_no_cuenta_lo_que_venia_de_antes(conexion):
    """Recortando a la última rueda, la posición vieja no es ganancia del período."""
    _velas(conexion, "GGAL", {"2026-01-05": 1000, "2026-01-06": 1200})
    _operacion(conexion, "compra", 100, 1000, "2026-01-05")

    totales = comparacion(conexion, desde="2026-01-06")["totales"]
    assert totales["aportado_neto"] == 0  # la compra fue antes del recorte
    assert totales["valor_actual"] == 120_000
    # Entró al período valiendo 100.000 (cierre del 05) y terminó en 120.000
    assert totales["ganancia"] == 20_000


def test_en_usd_el_mep_es_la_linea_plana(conexion):
    """Medido en dólares, quedarse en dólares no rinde: la referencia es 100."""
    _velas(conexion, "GGAL", {"2026-01-05": 1000, "2026-01-06": 1100})
    _tasas(conexion, "MEP", ("2026-01-05", 1000), ("2026-01-06", 1100))
    _operacion(conexion, "compra", 100, 1000, "2026-01-05")

    assert comparacion(conexion, moneda="USD")["benchmarks"]["mep"] == [100.0, 100.0]
    # En pesos sí se mueve: son pesos por dólar
    assert comparacion(conexion)["benchmarks"]["mep"] == [100.0, 110.0]


def test_en_usd_el_ccl_muestra_la_brecha_contra_el_mep(conexion):
    """El CCL medido en dólares MEP: cuánto se abrió la brecha entre los dos."""
    _velas(conexion, "GGAL", {"2026-01-05": 1000, "2026-01-06": 1100})
    _tasas(conexion, "MEP", ("2026-01-05", 1000), ("2026-01-06", 1000))
    _tasas(conexion, "CCL", ("2026-01-05", 1000), ("2026-01-06", 1200))
    _operacion(conexion, "compra", 100, 1000, "2026-01-05")

    # El MEP no se movió y el CCL subió 20%: la brecha se abrió 20 puntos
    assert comparacion(conexion, moneda="USD")["benchmarks"]["dolar"] == [100.0, 120.0]


def test_la_inflacion_solo_aparece_en_pesos(conexion):
    """En dólares no tiene sentido: la inflación es un fenómeno en pesos."""
    _velas(conexion, "GGAL", {"2026-01-05": 1000, "2026-01-06": 1100})
    _tasas(conexion, "MEP", ("2026-01-05", 1000), ("2026-01-06", 1000))
    guardar_inflacion(
        conexion,
        [{"fecha": "2025-12-31", "valor": 2.0}, {"fecha": "2026-01-31", "valor": 3.0}],
    )
    _operacion(conexion, "compra", 100, 1000, "2026-01-05")

    en_pesos = comparacion(conexion)
    # Las dos ruedas caen dentro del mismo mes: el índice todavía no cambió
    assert en_pesos["benchmarks"]["inflacion"] == [100.0, 100.0]
    assert "inflacion" not in comparacion(conexion, moneda="USD")["benchmarks"]


def test_endpoint_de_rendimiento(cliente, conexion):
    _velas(conexion, "GGAL", {"2026-01-05": 1000, "2026-01-06": 1100})
    _velas(conexion, "MERVAL", {"2026-01-05": 2_000_000, "2026-01-06": 2_200_000})
    _operacion(conexion, "compra", 100, 1000, "2026-01-05")

    datos = cliente.get("/api/cartera/rendimiento").json()
    assert datos["totales"]["twr_pct"] == 10.0
    assert datos["benchmarks"]["mercado"] == [100.0, 110.0]


def test_endpoint_de_rendimiento_valida_moneda_y_fecha(cliente):
    assert cliente.get("/api/cartera/rendimiento?moneda=EUR").status_code == 422
    assert cliente.get("/api/cartera/rendimiento?desde=05-01-2026").status_code == 422


def test_endpoint_de_realizado(cliente, conexion):
    _operacion(conexion, "compra", 100, 1000, "2026-01-05")
    _operacion(conexion, "venta", 100, 1500, "2026-01-06")

    datos = cliente.get("/api/cartera/realizado").json()
    assert datos["totales"]["pnl"] == 50_000
    assert datos["papeles"][0]["ticker"] == "GGAL"


def test_el_merval_en_dolares_se_convierte_con_el_mep(conexion):
    """En USD el benchmark de mercado es el índice dividido por el CCL."""
    _velas(conexion, "GGAL", {"2026-01-05": 1000, "2026-01-06": 1000})
    _velas(conexion, "MERVAL", {"2026-01-05": 2_000_000, "2026-01-06": 2_200_000})
    guardar_tasas(
        conexion,
        [
            {"fecha": "2026-01-05", "tipo": "MEP", "valor": 1000},
            {"fecha": "2026-01-06", "tipo": "MEP", "valor": 1100},
        ],
    )
    _operacion(conexion, "compra", 100, 1000, "2026-01-05")

    resultado = comparacion(conexion, moneda="USD")
    assert resultado["benchmarks"]["mercado"] == [100.0, 100.0]  # subió igual que el dólar
