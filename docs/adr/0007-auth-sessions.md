# ADR-0007 — Autenticación con sesiones opacas

**Contexto.** Necesitamos registro, login, logout, reset y perfil; la revocación debe ser
inmediata (logout, reset, cuentas comprometidas).

**Decisión.** Auth propia en FastAPI con sesiones opacas: token aleatorio de 256 bits en cookie
`HttpOnly; Secure; SameSite=Lax`, almacenado como SHA-256 en `sessions`. argon2id para contraseñas.
Frontend y API en el mismo sitio (rewrites de Next.js). CSRF con SameSite + cabecera double-submit.
Todo detrás de un módulo `identity` con interfaz clara para poder añadir OAuth/SSO (TEAM) más tarde.

**Alternativas.** JWT en el navegador (revocación difícil, riesgo de almacenamiento en JS);
proveedor gestionado (Auth0/Clerk: rápido, pero dependencia y coste; compatible más adelante como
otro proveedor de identidad).

**Consecuencias.** Somos responsables de rate limiting, reset y rotación: cubiertos por tests en la
Fase 1.
