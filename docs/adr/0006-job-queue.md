# ADR-0006 — Cola de trabajos

**Contexto.** Backtests e importaciones son CPU-bound y pueden durar minutos; el paper trading
necesita ticks programados. Requisito: Redis.

**Decisión.** **Dramatiq** sobre Redis, detrás de la interfaz `JobQueue` del backend. Estado del
job en PostgreSQL (fuente de verdad); Redis sólo como transporte. Colas separadas (`backtests`,
`paper_ticks`, `data_imports`), `time_limit` por actor, reintentos sólo para errores de
infraestructura. Scheduler de ticks como proceso separado que encola según calendario.

**Alternativas.** Celery (más pesado, configuración más frágil); RQ (menos control de límites y
middlewares); arq (asyncio, poco adecuado para trabajo CPU-bound).

**Consecuencias.** Cambiar de cola afecta sólo al adaptador. Los actores deben ser idempotentes.
