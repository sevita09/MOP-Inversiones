# Análisis transversal

La etapa v8 mira la cartera y el mercado **de costado**: no la evolución de un
papel en el tiempo, sino cómo se comportan entre sí y en qué momentos del año.
Todo se apoya en una base común: los retornos precalculados.

## Retornos precalculados (v8.1)

Tabla `retornos` (`ticker`, `temporalidad`, `moneda`, `ts`, `retorno`),
recalculada al final de cada sync.

### Por qué logarítmicos

```
r_t = ln(cierre_t / cierre_(t−1))
```

- **Se suman en el tiempo**: el retorno de un mes es la suma de sus días. Con
  retornos porcentuales habría que multiplicar `(1 + r)`.
- **Son simétricos**: subir 50% y bajar 50% no vuelve al inicio en porcentaje,
  pero `+ln(1,5)` y `−ln(1,5)` sí suman cero.
- **La correlación se calcula sobre ellos, nunca sobre precios**: dos series de
  precios con tendencia dan correlación alta aunque no tengan nada que ver.
- Pasar una serie a dólares es **restarle** el retorno del dólar.

### Las velas faltantes no generan retorno

Un placeholder o una vela interpolada no es un precio que existió: un retorno
calculado contra ella sería inventado. Si falta una rueda del medio, esa fecha
no tiene retorno y la serie sigue en la próxima vela real — sin fabricar el
salto de dos días como si fuera uno.

### Las dos monedas se guardan, no se derivan

Un retorno en pesos y uno en dólares responden preguntas distintas: en pesos la
estacionalidad la distorsiona la inflación, y en las correlaciones el factor
dólar común las infla a todas. La conversión usa `velas_para_vista` —la misma
del gráfico—, así los papeles con **ADR** usan la serie del certificado y no la
acción dividida por el CCL.

### Actualización incremental

`recalcular_todo` sigue desde el último retorno guardado de cada serie,
arrastrando una vela previa para poder encadenar el primero. El sync corre cada
15 minutos: rehacer diez años cada vez sería tirar trabajo a la basura.

Medido sobre la base real (200 tickers × D/S/M × ARS/USD):

| | |
|---|---|
| Carga inicial completa | 1.156.234 retornos en 23,8 s |
| Sync siguiente (sin datos nuevos) | 319 ms |

`recalcular_todo(completo=True)` fuerza la reconstrucción de toda la historia.

### Consultas

- `repositorios/retornos.obtener(ticker, temporalidad, moneda)` — la serie de un
  papel, que es lo que necesita la estacionalidad.
- `repositorios/retornos.alineados(tickers, temporalidad, moneda)` — la matriz
  `{ts: {ticker: retorno}}`, que es lo que necesitan las correlaciones. El
  índice `(temporalidad, moneda, ts)` está para esta consulta. Un papel que no
  operó ese día simplemente no aparece en esa fecha: quien consulta decide si
  descarta la fecha o la usa igual.
