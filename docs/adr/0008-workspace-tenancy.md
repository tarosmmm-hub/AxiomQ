# ADR-0008 — Tenancy por workspace

**Contexto.** El plan TEAM comparte estrategias. Añadir equipos más tarde sobre recursos que
pertenecen a usuarios obliga a migraciones de datos y cambios de autorización en todo el código.

**Decisión.** Todo recurso de negocio tiene `workspace_id`. En el registro se crea un workspace
`PERSONAL`. Las suscripciones pertenecen al workspace. Los repositorios exigen el workspace en cada
consulta.

**Consecuencias.** Algo más de complejidad inicial (membresías, roles), a cambio de que TEAM sea
una funcionalidad y no una migración.
