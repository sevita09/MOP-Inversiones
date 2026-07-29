"""Cartera: transacciones, tenencias, rendimiento.

**La cartera se valúa con el dólar MEP**, no con el CCL: es el dólar que se
consigue operando las dos puntas en BYMA (GGAL contra GGALD.BA), sin sacar la
plata del país, y por eso es el que corresponde a una cartera local. El resto de
la app (gráfico, indicadores, precios del sidebar) sigue usando el CCL.
"""
from app.repositorios.tasas_dolar import MEP

TIPO_DOLAR = MEP
