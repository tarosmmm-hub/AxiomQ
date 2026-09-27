# ADR-0001 — Monorepo y motor cuantitativo como librería pura

**Contexto.** El motor debe ser correcto, testeable aislado, reutilizable en backtest y paper
trading, y eventualmente ejecutable dentro de un sandbox. Si depende de FastAPI/SQLAlchemy, nada
de eso es posible.

**Decisión.** Monorepo con `frontend/`, `backend/`, `quant_engine/`, `workers/`, `data/`, `tests/`,
`infra/`. `quant_engine` es un paquete Python independiente que sólo depende de NumPy/pandas/SciPy
(y `exchange_calendars`). El backend lo usa exclusivamente a través de `EngineGateway`. Las reglas
de importación se verifican en CI con `import-linter`.

**Alternativas.** (a) Motor dentro del backend: más rápido al principio, acoplamiento irreversible.
(b) Motor como microservicio HTTP: aislamiento de proceso, pero latencia y operación extra sin
necesidad en MVP; el diseño actual permite hacerlo después.

**Consecuencias.** Tipos duplicados en la frontera (modelos ORM ↔ tipos del motor) mediante
mapeadores explícitos. A cambio: tests del motor sin BD y posibilidad de sandbox.
