# Plan de implementación por fases

Regla de avance: una fase se cierra sólo cuando (1) sus tests pasan en CI, (2) lint/typecheck
limpios, (3) se revisó la arquitectura frente a `ARCHITECTURE.md` y se actualizaron docs/ADRs, y
(4) no hay errores críticos abiertos. Los tests se escriben **dentro** de cada fase; la Fase 9
completa huecos y E2E, no es el primer momento en que se testea.

---

## Fase 0 — Análisis y arquitectura ✅ (este entregable)

`ARCHITECTURE.md`, ADRs, `METRICS.md`, `RISKS.md`, este plan.

## Fase 1 — Infraestructura + base de datos + auth ✅ (ver `docs/CHANGELOG.md`)

- Monorepo: workspace `uv` (`quant_engine`, `backend`, `workers`), `pnpm` para `frontend`.
- Docker Compose: postgres, redis, backend, worker, frontend, mailpit. Dockerfiles non-root.
- `Makefile` + `scripts/`: install, dev, test, lint, build, migrate, seed.
- Ruff, mypy, ESLint, TS strict, import-linter; GitHub Actions (lint + unit + integración + migraciones).
- Backend: app factory, settings, logging JSON, errores problem+json, healthchecks.
- Alembic: migración inicial con `users`, `workspaces`, `workspace_members`, `sessions`,
  `user_tokens` (reset de contraseña y verificación de email), `plans`, `plan_entitlements`, `subscriptions`, `audit_log`,
  `analytics_events`.
- Módulos `identity`, `workspaces`, `billing` (entitlements), `analytics` (sink).
- Frontend: layout, tema claro/oscuro, design tokens, páginas register/login/forgot/reset/profile.
- **Salida**: tests de hashing, sesiones, reset (expiración, un solo uso, revocación), CSRF, rate
  limit, entitlements, aislamiento de workspaces; migraciones upgrade/downgrade en CI.

## Fase 2 — Market data

- `quant_engine.data`: tipos (`Bar`, `BarSeries`, `Timeframe`, `CorporateAction`),
  `MarketDataProvider`, `MockDataProvider`, `HistoricalCSVProvider` + manifiesto, validación,
  calendarios.
- Migración: `assets`, `datasets`, `market_data`, `corporate_actions`.
- Job `data_import`, `DatabaseProvider`, endpoints de assets/datasets/barras.
- Dataset sintético de desarrollo generado por script determinista y etiquetado `SYNTHETIC`.
- Mercado chileno: calendario `XSGO`, activos IPSA de referencia (metadatos, sin precios),
  `index_memberships` point-in-time, normalización de símbolos (`.SN` → local), formato CLP.
- UI: gestor de datos (lista de datasets, proveniencia, insignia, vista de precio).
- **Salida**: tests de validación (cada regla), de calendario (festivos, DST), de proveniencia, de
  import idempotente.

## Fase 3 — Quant engine (núcleo)

- Tipos de órdenes/fills, `FillModel` next-bar-open, slippage, comisión, `Ledger` Decimal,
  posiciones, splits/dividendos, reglas de riesgo pre-trade, sizers.
- `Strategy` protocol, contexto de sólo lectura, indicadores (SMA, EMA, RSI), `StrategySpec` +
  compilador + validador; `BuyAndHold`.
- **Salida**: tests unitarios de cada pieza, property tests contables, test de invariancia a datos
  futuros para cada indicador y estrategia.

## Fase 4 — Backtesting

- `BacktestRunner` (bucle event-driven), `BacktestResult`, benchmark buy & hold.
- Migración: `strategies`, `strategy_versions`, `experiments`, `backtests`, `portfolios`, `orders`,
  `fills`, `trades`, `positions`, `backtest_equity_points`, `diagnostics`.
- `EngineGateway`, `JobQueue` (Dramatiq), actor `run_backtest` con límites, endpoints.
- UI: Strategy Builder (formulario del spec), lanzar backtest, estado.
- **Salida**: golden tests de backtests completos, test de integración API → cola → worker → BD.

## Fase 5 — Métricas

- `quant_engine.metrics` según `METRICS.md`, `diagnostics` anti-sesgo, `backtest_metrics`.
- UI: página de resultados (equity, drawdown, retornos mensuales, distribución, estadísticas, lista
  de trades, exposición, riesgo, vs buy & hold).
- **Salida**: tests obligatorios por métrica (ver `METRICS.md`).

## Fase 6 — Dashboard

- Endpoint agregado `/dashboard/summary`; UI: estrategias, últimos backtests, paper, experimentos
  recientes, paleta de comandos.
- Comparación de estrategias (tabla neutral + gráficos comparativos).
- **Salida**: tests de agregación y de componentes; no se mezclan cifras de modos distintos.

## Fase 7 — Experiment tracking

- Registro completo (hashes, versión de motor), re-ejecución y verificación de `result_hash`,
  historial por estrategia, contador de ensayos (`MANY_TRIALS`).
- **Salida**: test de reproducibilidad (re-run produce `result_hash` idéntico).

## Fase 8 — Paper trading

- `PaperBroker`, `PaperSession`, scheduler de ticks por calendario, idempotencia por barra,
  `paper_accounts`, `paper_snapshots`, UI de cuenta paper.
- **Salida**: tests de tick idempotente, de reanudación tras caída, de equivalencia
  (mismos datos → paper replay = backtest).

## Fase 9 — Testing

- E2E Playwright: Register → Create Strategy → Run Backtest → View Results; flujo paper.
- Revisión de cobertura por riesgo, tests de seguridad (tenancy, auth), carga ligera de la cola.

## Fase 10 — Production hardening

- CSP/HSTS, rate limits revisados, `pip-audit`/`pnpm audit`, SBOM, imágenes mínimas read-only,
  backups y restore probado, retención de analytics, runbooks, observabilidad, límites por plan
  revisados, checklist de seguridad (OWASP ASVS nivel 2 como guía).
