# Contribuir a AxiomQ

Prioridad de ingeniería: **CORRECTNESS > SECURITY > MAINTAINABILITY > PERFORMANCE > FEATURES**.

## Flujo

1. Rama desde `main` (`feat/...`, `fix/...`, `docs/...`).
2. Cambios pequeños y revisables; un PR = una intención.
3. `make lint` y `make test` en verde antes de abrir el PR (CI ejecuta además E2E y build de
   imágenes).
4. Si cambias la API: `make api-client` y commitea `frontend/src/lib/api/schema.d.ts`.
5. Si cambias modelos: `make migration m="..."`, **revisa la migración a mano** y comprueba
   `alembic downgrade -1 && alembic upgrade head`. Nunca `create_all` ni tablas creadas desde
   endpoints.
6. Si tomas una decisión difícil de revertir: añade un ADR en `docs/adr/`.

## Reglas no negociables

- **Nada de datos inventados.** Ningún número presentado al usuario como resultado puede venir de
  aleatoriedad o de valores fijos. Datos sintéticos sólo en tests o datasets etiquetados
  `SYNTHETIC`.
- **Separación de modos**: backtest, paper y live nunca comparten portfolios, órdenes ni totales.
- **Motor puro**: `quant_engine` no importa backend, SQLAlchemy, FastAPI, Redis ni Dramatiq
  (lo verifica `lint-imports`).
- **Endpoints finos**: los routers validan, autorizan y delegan; la lógica vive en servicios y la
  lógica cuantitativa en `quant_engine`.
- **Tenancy**: toda consulta de datos de negocio se filtra por workspace en la capa de servicio o
  repositorio, con test de aislamiento.
- **Nada de ejecución de código de usuario** fuera del futuro sandbox (ADR-0002).
- **Métricas**: toda métrica nueva se especifica primero en `docs/METRICS.md`, con test calculado a
  mano y tests de casos límite; si no se puede calcular, devuelve `None` + motivo.
- **Secretos**: nunca en el repo. Configuración por variables `AXIOMQ_*`.

## Estilo

- Python: Ruff (lint + formato, 100 columnas), mypy strict en código de aplicación, tipos en
  todas las funciones públicas.
- TypeScript: strict + `noUncheckedIndexedAccess`, ESLint (config de Next.js), Prettier.
- Código e identificadores en inglés; documentación de arquitectura en español.
- Commits en imperativo, explicando el *porqué* cuando no es obvio.

## Tests

| Tipo | Dónde | Requiere |
|---|---|---|
| Unit Python | `*/tests/unit`, `quant_engine/tests` | nada |
| Integración | `backend/tests/integration`, `workers/tests` (marcador `integration`) | PostgreSQL + Redis |
| E2E | `tests/e2e` | PostgreSQL; levanta API y web automáticamente |

La base de datos de tests se recrea desde las migraciones en cada ejecución
(`AXIOMQ_TEST_DATABASE_URL`, por defecto `axiomq_test` en localhost).
