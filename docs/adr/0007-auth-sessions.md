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

**Implementación (Fase 1).**
- El registro responde siempre `202` y **no** inicia sesión: si el email ya existe se envía al
  buzón un aviso en lugar de un enlace de verificación, y se hace el mismo trabajo de hashing para
  que el tiempo de respuesta no revele la existencia de la cuenta. El usuario inicia sesión
  después (se permite con email sin verificar; la verificación se exige para lanzar backtests).
- Tokens de email en una tabla única `user_tokens` (`PASSWORD_RESET`, `EMAIL_VERIFICATION`),
  hash SHA-256, un solo uso, un token activo por propósito.
- El reset de contraseña revoca todas las sesiones y marca el email como verificado.
- IP de cliente: `X-Forwarded-For` sólo se usa con `AXIOMQ_TRUSTED_PROXY_HOPS > 0`, contando desde
  la derecha. El proxy de Next.js reenvía la cabecera sin añadir entradas, así que no cuenta
  como salto.
