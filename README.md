# AxiomQ

Plataforma de infraestructura cuantitativa para crear, ejecutar, comparar y analizar estrategias
de trading algorítmico (backtesting, paper trading y experiment tracking) sin dinero real.
Mercados objetivo del MVP: acciones/ETFs de EE. UU. y acciones chilenas (universo IPSA).

> **Estado: Fase 1 completada** (infraestructura, base de datos, autenticación, planes).
> El motor cuantitativo, los datos de mercado y los backtests llegan en las Fases 2–5
> ([plan](docs/IMPLEMENTATION_PLAN.md)). La interfaz nunca muestra resultados que no hayan sido
> calculados de verdad: los módulos aún no construidos aparecen deshabilitados.

Los resultados de la plataforma son simulaciones y no garantizan rentabilidad futura. AxiomQ no
ejecuta operaciones con dinero real.

## Stack

| Capa | Tecnología |
|---|---|
| Frontend | Next.js 16 (App Router), TypeScript strict, Tailwind CSS 4, TanStack Query |
| API | FastAPI, Pydantic 2, SQLAlchemy 2 (psycopg 3), Alembic |
| Motor cuantitativo | Python, NumPy, pandas (librería pura, sin dependencias web/BD) |
| Jobs | Dramatiq sobre Redis |
| Base de datos | PostgreSQL 16 |
| Calidad | Ruff, mypy (strict), import-linter, ESLint, Prettier, Pytest, Playwright |
| Infra | Docker, Docker Compose, GitHub Actions |

## Requisitos

- Docker + Docker Compose (camino recomendado), **o** localmente:
- Python ≥ 3.11 con [uv](https://docs.astral.sh/uv/), Node ≥ 20.9 con pnpm 10,
  PostgreSQL 16 y Redis 7.

## Puesta en marcha

### Opción A — todo en Docker

```bash
cp .env.example .env
make dev            # web :3000 · api :8000 (docs en /api/v1/docs) · mailpit :8025
make seed           # (otra terminal, opcional) usuario demo@axiomq.local
```

Los emails (verificación, reset de contraseña) se ven en Mailpit: <http://localhost:8025>.

### Opción B — apps locales, servicios en Docker

```bash
cp .env.example .env
make install        # uv sync + pnpm install
make services       # postgres, redis, mailpit
make migrate
make seed
make api            # terminal 1
make worker         # terminal 2
make web            # terminal 3 → http://localhost:3000
```

## Comandos

| Comando | Qué hace |
|---|---|
| `make install` | Instala dependencias Python (uv) y Node (pnpm) |
| `make dev` | Levanta el stack completo en Docker |
| `make test` | Tests Python unitarios + integración (requiere PostgreSQL y Redis) |
| `make test-unit` | Sólo tests unitarios (sin base de datos) |
| `make test-e2e` | Build del frontend + Playwright contra el stack real |
| `make lint` | Ruff, formato, mypy, contratos de arquitectura, ESLint, tsc, Prettier |
| `make build` | Imágenes Docker de producción |
| `make migrate` | Aplica migraciones Alembic |
| `make migration m="..."` | Genera una migración nueva (revisar siempre a mano) |
| `make seed` | Datos de desarrollo (se niega a correr en producción) |
| `make api-client` | Regenera el cliente TypeScript desde el OpenAPI del backend |

Variables de entorno: ver [`.env.example`](.env.example).

## Estructura

```
frontend/      Next.js — UI, proxy /api → backend (src/proxy.ts)
backend/       FastAPI — módulos identity, workspaces, billing, analytics, audit; migraciones
quant_engine/  Motor cuantitativo (librería pura; se construye en las Fases 2–5)
workers/       Actores Dramatiq (trabajos largos: backtests, ticks de paper trading, imports)
data/          Datasets de fixtures con procedencia documentada
tests/e2e/     Playwright
infra/         Dockerfiles y Docker Compose
scripts/       Utilidades de desarrollo
docs/          ADRs, métricas, riesgos, plan, changelog por fase
```

## Documentación

- [ARCHITECTURE.md](ARCHITECTURE.md) — arquitectura completa y puntos de extensión
- [CONTRIBUTING.md](CONTRIBUTING.md) — flujo de trabajo y reglas de ingeniería
- [docs/IMPLEMENTATION_PLAN.md](docs/IMPLEMENTATION_PLAN.md) — fases y criterios de salida
- [docs/CHANGELOG.md](docs/CHANGELOG.md) — qué se entregó y revisó en cada fase
- [docs/RISKS.md](docs/RISKS.md) — riesgos técnicos y decisiones difíciles de revertir
- [docs/METRICS.md](docs/METRICS.md) — definición matemática de cada métrica
- [docs/adr/](docs/adr/) — Architecture Decision Records
