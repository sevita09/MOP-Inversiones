"""Configuración central: universo de tickers, temporalidades y EMAs."""

PANEL_LIDER = [
    "ALUA", "BMA", "BYMA", "CEPU", "COME", "CRES", "EDN", "GGAL", "LOMA",
    "MIRG", "PAMP", "SUPV", "TECO2", "TGNO4", "TGSU2", "TRAN", "TXAR",
    "VALO", "YPFD",
]

PANEL_GENERAL = [
    "AGRO", "AUSO", "BHIP", "BPAT", "CARC", "CELU", "CECO2", "CTIO",
    "DGCU2", "FERR", "HAVA", "INVJ", "IRSA", "LEDE", "LONG", "METR",
    "MOLA", "MOLI", "MORI", "OEST", "SAMI",
]

CEDEARS = ["AAPL"]

# ADR de GGAL en NYSE: solo se usa para calcular la tasa CCL, no se muestra en la UI
TICKER_CCL_BASE = "GGALD"

# Tickers sintéticos de dólar (se generan en v0.5)
TICKERS_DOLAR = ["DOLARCCL", "DOLAROF"]

# Temporalidades: H = hora, D = día, S = semana, M = mes
# Código yfinance equivalente, solo para la descarga
INTERVALO_YFINANCE = {
    "H": "1h",
    "D": "1d",
    "S": "1wk",
    "M": "1mo",
}

# Cuánta historia se descarga la primera vez (después la base solo apendea)
HISTORIA_POR_TEMPORALIDAD = {
    "H": "2y",
    "D": "10y",
    "S": "10y",
    "M": "10y",
}

TEMPORALIDADES = list(HISTORIA_POR_TEMPORALIDAD)

# La EMA central de la metodología depende de la temporalidad
EMA_POR_TEMPORALIDAD = {
    "D": 200,
    "S": 50,
    "M": 12,
    "H": 200,
}

# La temporalidad horaria queda fuera del motor de bots por diseño
TEMPORALIDADES_BOTS = ["D", "S", "M"]


def tickers_byma() -> list:
    return PANEL_LIDER + PANEL_GENERAL


def todos_los_tickers() -> list:
    return tickers_byma() + CEDEARS + [TICKER_CCL_BASE]
