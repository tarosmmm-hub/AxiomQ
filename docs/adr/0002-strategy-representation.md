# ADR-0002 — Representación de estrategias

**Contexto.** El usuario debe crear estrategias hoy (MA cross, umbrales) y, en el futuro, subir
código. Ejecutar código arbitrario en el servidor es inaceptable sin sandbox.

**Decisión.**
1. MVP: **spec declarativo JSON** (catálogo cerrado de indicadores, comparadores y operadores
   lógicos), con `schema_version`, validado en backend y motor, compilado a un objeto `Strategy`.
   Sin `eval`, sin expresiones de texto libre, sin plantillas.
2. Estrategias internas (p. ej. `BuyAndHold`) implementan el protocolo Python `Strategy`
   (`initialize`, `on_bar`, `on_fill`) con un contexto de sólo lectura.
3. Versiones inmutables (`strategy_versions`, `spec_hash`).
4. Futuro código de usuario: `SandboxedStrategyRuntime` que ejecuta el protocolo en un proceso
   aislado (contenedor gVisor/Firecracker efímero por job, sin red, FS read-only + tmpfs, límites
   cgroup CPU/memoria/pids, timeout duro, usuario sin privilegios, sólo stdlib + lista blanca de
   librerías). El motor habla con él por un protocolo serializado (barra → intents). Los procesos
   API/worker normales nunca importan código de usuario. `RestrictedPython` o `exec` con builtins
   recortados **no** se consideran sandbox.

**Alternativas.** DSL de texto tipo Pine Script (requiere parser propio, más superficie de ataque);
código Python desde el día 1 (inseguro sin la infraestructura de sandbox).

**Consecuencias.** Expresividad limitada en el MVP, a cambio de seguridad total y de specs
fáciles de validar, versionar, comparar y renderizar en la UI.
