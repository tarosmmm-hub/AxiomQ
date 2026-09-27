# Changelog por fases

## Fase 1 — Infraestructura, base de datos y autenticación (2026-09-27)

### Entregado

**Monorepo y tooling**
- Workspace `uv` (`quant_engine`, `backend`, `workers`) y `pnpm` (`frontend`, `tests/e2e`).
- `Makefile` con `install · dev · services · api · worker · web · test · test-unit · test-e2e ·
  lint · format · build · migrate · migration · seed · api-client`.
- Ruff, mypy strict, import-linter (contratos: motor puro; sólo el adaptador de cola conoce
  Dramatiq), ESLint, TypeScript strict + `noUncheckedIndexedAccess`, Prettier.
- CI en GitHub Actions: Python (lint, tipos, contratos, tests con Postgres/Redis), frontend
  (lint, tipos, build, contrato OpenAPI), E2E Playwright e imágenes Docker.

**Infraestructura**
- Dockerfile Python único (API, worker, migraciones): `dev` editable, `runtime` sin dependencias
  de desarrollo, usuario no-root, healthcheck. Dockerfile frontend con salida `standalone`, no-root.
- Docker Compose de desarrollo: postgres, redis, mailpit, migrate, api (reload), worker (watch),
  web (hot reload).

**Backend**
- App factory, configuración 12-factor validada (rechaza configuraciones inseguras en
  producción), logs JSON con `request_id`, errores `application/problem+json`, `/healthz` y
  `/readyz`.
- Migración inicial: `users`, `sessions`, `user_tokens`, `workspaces`, `workspace_members`,
  `plans`, `plan_entitlements`, `subscriptions`, `audit_log`, `analytics_events` + catálogo de
  planes FREE/PRO/TEAM.
- Auth: registro (anti-enumeración), login, logout, sesiones opacas con hash, CSRF double-submit
  firmado, verificación de email, reset de contraseña, cambio de contraseña, perfil, rate
  limiting (Redis), auditoría de eventos de seguridad.
- Workspaces personales creados en el registro; aislamiento entre tenants (404, no 403).
- Entitlements leídos de BD (`/me/entitlements`), `ensure_quota` / `ensure_feature` listos para
  la Fase 4; fallback a FREE si la suscripción está cancelada; cuota desconocida = 0 (fail closed).
- Analytics: catálogo cerrado de eventos con propiedades en lista blanca, `user_ref`
  pseudónimo, opt-out por workspace.
- Jobs: puerto `JobQueue`, adaptador Dramatiq, worker con actor `system.ping` (verifica BD).
- CLI: `seed` (usuario demo, nunca en producción) y `openapi`.

**Frontend**
- Next.js 16: `src/proxy.ts` (proxy `/api` en runtime + redirección de páginas protegidas),
  cliente tipado generado desde OpenAPI (`openapi-fetch`) con CSRF automático.
- Design tokens claro/oscuro sin parpadeo, componentes (`Button`, `Field`, `Panel`, `Badge`,
  `Alert`), app shell responsive.
- Páginas: login, registro, olvidé mi contraseña, reset, verificación de email, dashboard, ajustes
  (perfil y contraseña). El dashboard sólo muestra datos reales (plan, límites, estado de
  verificación) y estados vacíos para módulos futuros; mercados EE. UU. (XNYS/USD) y Chile
  (XSGO/CLP) como configuración, sin precios.

### Verificación

| Check | Resultado |
|---|---|
| `pytest` (unit + integración, Postgres + Redis reales) | 78 passed |
| Playwright E2E (registro → login → dashboard → perfil → logout → redirect protegido; credenciales erróneas; contraseña débil; open redirect) | 4 passed |
| Ruff lint + format, mypy strict, import-linter | limpio (2 contratos respetados) |
| ESLint, `tsc --noEmit`, Prettier, `next build` | limpio |
| Migraciones: upgrade → downgrade → upgrade, modelos == migraciones | OK |
| Imagen Python runtime: migra, sirve la API y el worker consume un job enviado por el adaptador de la API; usuario 10001 | OK |
| Imagen frontend runtime: sirve login, redirige anónimos, proxy `/api` en runtime; usuario 10001 | OK |

### Revisión de arquitectura y hallazgos

- **Cookie de sesión con `Expires` absoluto** calculado con el reloj del servidor: se cambió a
  `Max-Age` relativo (la expiración autoritativa es `sessions.expires_at`).
- **IP de cliente detrás de proxies**: el proxy de Next.js reenvía `X-Forwarded-For` tal como lo
  envía el cliente (comprobado). Se sustituyó "confiar en la primera entrada" por
  `AXIOMQ_TRUSTED_PROXY_HOPS` contando desde la derecha; por defecto se ignora la cabecera.
  Consecuencia en desarrollo: los límites por IP se comparten detrás del proxy; los límites por
  email siguen siendo efectivos. En producción debe configurarse el número de balanceadores.
- **Timing del registro**: la rama "email ya existe" también ejecuta argon2 para no revelar la
  existencia de la cuenta por tiempo de respuesta; los emails se envían en background tras el
  commit.
- **Ruff formateaba bloques de código dentro de Markdown** (y rompía ejemplos en
  `ARCHITECTURE.md`): se excluyeron los `.md` de Ruff.

### Pendiente / deuda consciente

- CSP del frontend con nonces (Fase 10). La API ya envía CSP estricta.
- Lista de contraseñas comunes reducida (≈70 entradas); ampliar con una lista de frecuencia de
  filtraciones en la Fase 10.
- Cambio de email del usuario (requiere re-verificación): no incluido.
- Equipos (TEAM): el modelo de workspaces y membresías existe; invitaciones y gestión de miembros
  llegan con la funcionalidad de estrategias compartidas.
