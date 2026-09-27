# ADR-0010 — SQLAlchemy síncrono en API y workers

**Contexto.** FastAPI admite endpoints async; los workers (Dramatiq) son síncronos y CPU-bound.
Mantener dos stacks de acceso a datos (async en API, sync en workers) duplicaría repositorios y
servicios.

**Decisión.** SQLAlchemy 2 síncrono con psycopg 3 en todo el backend. Los endpoints son funciones
`def` que FastAPI ejecuta en su thread pool. Cada request usa un `UnitOfWork`; los handlers hacen
`commit` explícito **antes** de responder, y los efectos secundarios (emails) se difieren hasta
después del commit y se ejecutan como background tasks.

**Alternativas.** Async (`asyncpg`) en la API: mejor para miles de conexiones concurrentes de
larga espera, que no es nuestro perfil (el trabajo pesado va a workers).

**Consecuencias.** Un único código de servicios/repositorios. Si en el futuro hiciera falta alta
concurrencia de I/O (p. ej. streaming de precios), se aislará en un servicio específico.
