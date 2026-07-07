"""Configuración central: universo de tickers, temporalidades y EMAs."""

from typing import Optional

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

# CEDEARs: subyacentes del exterior (cotizan en su moneda de origen, sin conversión).
# Validados contra Yahoo Finance. Algunos usan un símbolo distinto allá: ver
# YAHOO_OVERRIDE en servicios/descarga.py (DISN→DIS, BRKB→BRK-B, PETR3→.SA, etc.).
CEDEARS = [
    "AAPL", "MU", "SPY", "VIST", "MSFT", "MSTR", "KO", "NVDA", "QQQ", "MELI",
    "ORCL", "NU", "META", "AMD", "SNDK", "SPCX", "V", "RKLB", "IBIT", "GOOGL",
    "AMZN", "TSLA", "GLD", "IREN", "INTC", "NOW", "BRKB", "IBM", "NBIS", "KEEL",
    "HUT", "EWZ", "ASTS", "PLTR", "MCD", "GLOB", "NFLX", "PBR", "AVGO", "MA",
    "COIN", "TSM", "BABA", "CRM", "WFC", "SATL", "XLV", "LAR", "SMH", "RGTI",
    "JPM", "WMT", "EEM", "QCOM", "STNE", "XLF", "XP", "SLV", "ADBE", "PAGS",
    "XLE", "CRWV", "ASML", "COPX", "GPRK", "VST", "AMAT", "GLW", "ARCO", "RSP",
    "ETHA", "JNJ", "DIA", "IVV", "UBER", "UNH", "RACE", "ACWI", "PFE", "LLY",
    "NKE", "PANW", "RIOT", "XLP", "SPCE", "AXP", "ALAB", "MRVL", "PEP", "ANF",
    "RBLX", "B", "VEA", "CEG", "CVX", "CAT", "EBAY", "BBD", "HMY",
    "TQQQ", "PG", "HIMS", "MRNA", "SH", "XLU", "BAK", "GDX", "C", "OKLO", "VZ",
    "UPST", "NIO", "MO", "IVE", "ABT", "ACN", "ANET", "UL", "AMX", "URA", "BA",
    "PAAS", "BB", "LMT", "FXI", "O", "UGP", "CIBR", "TRIP", "ROKU", "CSCO",
    "FSLR", "TEN", "LRCX", "TEAM", "IWM", "TM", "TWLO", "BIDU", "XLK",
    "EWY", "T", "SPOT", "VIG", "AAL", "ONDS", "JD", "VALE", "HOOD",
    "GT", "RTX", "ARM", "KMB", "DISN",
]

# ADR de GGAL en NYSE: solo se usa para calcular la tasa CCL, no se muestra en la UI
TICKER_CCL_BASE = "GGALD"

# Tickers sintéticos de dólar (se generan en v0.5)
TICKERS_DOLAR = ["DOLARCCL", "DOLAROF"]

# Acciones locales que además cotizan en el exterior como ADR.
# byma -> (símbolo del ADR en Yahoo, acciones locales por cada ADR).
# En USD estas se muestran con el precio real del ADR (no la acción ÷ CCL).
ADR = {
    "GGAL": ("GGAL", 10), "YPFD": ("YPF", 1), "BMA": ("BMA", 10),
    "SUPV": ("SUPV", 5), "PAMP": ("PAM", 25), "TGSU2": ("TGS", 5),
    "CEPU": ("CEPU", 10), "EDN": ("EDN", 20), "LOMA": ("LOMA", 5),
    "TECO2": ("TEO", 5), "CRES": ("CRESY", 10), "IRSA": ("IRS", 10),
}
# La serie del ADR se guarda bajo "{byma}.ADR" (el símbolo del ADR suele
# coincidir con el de la acción local, p.ej. SUPV, y chocaría en la base).
SUFIJO_ADR = ".ADR"


def adr_de(ticker: str) -> Optional[dict]:
    """Info del ADR de una acción local: {simbolo, ratio}, o None si no tiene."""
    if ticker in ADR:
        simbolo, ratio = ADR[ticker]
        return {"simbolo": simbolo, "ratio": ratio}
    return None

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


def periodo_ema_central(temporalidad: str) -> int:
    """Período de la EMA central de la metodología para una temporalidad."""
    return EMA_POR_TEMPORALIDAD[temporalidad]


def tickers_byma() -> list:
    return PANEL_LIDER + PANEL_GENERAL


def todos_los_tickers() -> list:
    return tickers_byma() + CEDEARS + [TICKER_CCL_BASE]
