# Especificación de métricas

Este documento es la **fuente de verdad** de cada métrica. El código (`quant_engine/metrics/`) y
los tests referencian estas definiciones. Si el código y este documento discrepan, es un bug.

## Convenciones

- **Serie de equity** `E_0, E_1, …, E_T`: valor del portfolio (cash + posiciones a precio de cierre)
  al cierre de cada barra del rango. `E_0` = capital inicial, registrado al cierre de la primera
  barra (antes de cualquier fill, que como pronto ocurre en la barra 1).
- **Retornos por periodo** (simples): `r_t = E_t / E_{t−1} − 1`, `t = 1..T`, `n = T`.
- **Periodos por año** `P`: derivado del calendario del activo y el timeframe. `1D` en mercado de
  EE. UU. → `P = 252`; activos 24/7 con `1D` → `P = 365`; Bolsa de Santiago (`XSGO`) → número medio de sesiones por año
  del calendario en el rango del backtest (redondeado a entero y guardado). Se guarda en el experimento.
- **Años transcurridos** `Y = (ts_T − ts_0) / 365.25 días` (tiempo calendario, no número de barras).
- **Tasa libre de riesgo** `rf` anual, parámetro del experimento (por defecto `0`), convertida a
  por-periodo: `rf_p = (1 + rf)^(1/P) − 1`.
- **Trades**: ciclos cerrados de posición (ver ARCHITECTURE §5.4). `pnl_i` es neto de comisiones y
  slippage. Las posiciones abiertas al final **no** cuentan.
- Desviación típica muestral con `ddof = 1`.
- Resultado de cada función: `MetricResult(value: float | None, reason: str | None)`. Si
  `value is None`, `reason` explica por qué y la UI muestra `—` con el motivo. **Nunca** se
  sustituye por 0, ∞ o un valor por defecto.
- Precondiciones del motor (no casos de métrica): `E_0 > 0`, sin NaN/inf en la equity. Si se
  violan, el backtest falla con error; no se calculan métricas.

## Métricas de rendimiento

| Clave | Definición | Indefinida cuando |
|---|---|---|
| `total_return` | `E_T / E_0 − 1` | `T = 0` |
| `cagr` | `(E_T / E_0)^(1/Y) − 1`; si `E_T = 0` → `−1` | `Y < 1` (anualizar menos de un año extrapola; se muestra `total_return`) |
| `volatility` | `std(r, ddof=1) · √P` | `n < 2` |
| `sharpe` | `mean(r − rf_p) / std(r − rf_p, ddof=1) · √P` | `n < 2` o `std = 0` |
| `sortino` | `mean(r − rf_p) / DD · √P`, con `DD = √( (1/n) Σ min(0, r_t − rf_p)² )` (denominador `n` = todos los periodos) | `n < 2` o `DD = 0` (no hay periodos por debajo del objetivo) |
| `max_drawdown` | `min_t (E_t / max_{s≤t} E_s − 1)` (valor ≤ 0); se reporta además la duración máxima en barras y en días | `T = 0` |
| `calmar` | `cagr / |max_drawdown|` sobre todo el periodo (no la ventana de 36 meses clásica; documentado en la UI) | `cagr` indefinida o `max_drawdown = 0` |

## Métricas de trades

| Clave | Definición | Indefinida cuando |
|---|---|---|
| `num_trades` | número de trades cerrados | nunca (puede ser 0) |
| `win_rate` | `#{pnl_i > 0} / num_trades` (pnl = 0 no cuenta como ganador) | `num_trades = 0` |
| `profit_factor` | `Σ pnl_i⁺ / |Σ pnl_i⁻|` | `num_trades = 0` o no hay trades perdedores |
| `avg_trade_pnl` | `mean(pnl_i)` en moneda del portfolio | `num_trades = 0` |
| `avg_trade_return` | `mean(ret_i)`, `ret_i = pnl_i / coste_entrada_i` (coste incluye comisión de entrada) | `num_trades = 0` |
| `best_trade` / `worst_trade` | `max(ret_i)` / `min(ret_i)` (+ pnl asociado) | `num_trades = 0` |

## Métricas de exposición y riesgo

| Clave | Definición | Indefinida cuando |
|---|---|---|
| `time_in_market` | fracción de barras `1..T` con posición ≠ 0 al cierre | `T = 0` |
| `avg_gross_exposure` | `mean_t( Σ|qty·close| / E_t )` | `T = 0` |
| `max_leverage` | `max_t( Σ|qty·close| / E_t )` | `T = 0` |
| `max_concentration` | `max_t max_asset( |qty·close| / Σ|qty·close| )` en barras con posición | sin posiciones |

## Series derivadas

- **Retornos mensuales**: `E_fin_mes / E_fin_mes_anterior − 1`, usando el último cierre de cada mes
  natural (zona horaria del exchange). El primer y el último mes, si son parciales, se marcan como
  parciales.
- **Drawdown**: `DD_t` de la definición anterior, por barra.
- **Distribución de trades**: histograma de `ret_i`, con los bordes calculados sobre los datos (no
  bins fijos que oculten colas).

## Tests obligatorios por métrica

1. Caso calculado a mano (serie de 3–10 puntos) con tolerancia relativa `1e-12`.
2. Todos los casos de la columna "indefinida cuando".
3. Serie constante, serie monótona creciente, caída a cero (`E_T = 0`).
4. Contraste con implementación de referencia independiente (fórmula directa en NumPy vs. la
   función) sobre series aleatorias generadas por Hypothesis — *sólo* como test de la función, nunca
   como datos presentados al usuario.
