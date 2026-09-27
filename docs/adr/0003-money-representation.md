# ADR-0003 — Representación de dinero

**Contexto.** La contabilidad (cash, cantidades, comisiones, P&L) debe cuadrar exactamente y ser
auditable; la analítica (retornos, volatilidad) es estadística y necesita NumPy.

**Decisión.** `Decimal` (contexto con 28 dígitos, redondeo `ROUND_HALF_EVEN`) en el `Ledger` y en
órdenes/fills; `float64` para valoración por barra, series y métricas; `NUMERIC(24,10)` en
PostgreSQL. La conversión ocurre en un único punto (`portfolio.valuation`) y está testeada.

**Alternativas.** Todo `float64` (simple y rápido, pero errores acumulados en el cash y
comparaciones inexactas en tests contables); todo `Decimal` (lento e incompatible con NumPy);
enteros en unidades mínimas (complica precios con muchos decimales, p. ej. cripto).

**Consecuencias.** Coste de rendimiento acotado: los fills son escasos frente al número de barras.
Invariantes contables comprobables con igualdad exacta.
