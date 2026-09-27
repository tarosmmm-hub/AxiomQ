# Riesgos técnicos, decisiones difíciles de revertir y preguntas abiertas

## 1. Riesgos técnicos

| # | Riesgo | Impacto | Mitigación |
|---|---|---|---|
| R1 | **Errores numéricos silenciosos** en el motor o métricas (off-by-one en retornos, fill en la barra equivocada, doble cómputo de comisión) | Crítico: resultados falsos = producto sin valor y engañoso | Especificación escrita (`METRICS.md`), tests a mano, property tests de invariantes contables, golden tests revisados, test de invariancia a datos futuros |
| R2 | **Look-ahead sutil**: series back-adjusted, indicadores centrados, fill al close de la barra de señal, universo con constituyentes actuales | Crítico | Timestamps = cierre, fill en `i+1`, ajuste *as-of*, vistas truncadas, test de invariancia, aviso de supervivencia |
| R3 | **Licencia de datos**: redistribuir datos de Yahoo/otros en el repo o en el SaaS | Legal | Manifiesto con `license` obligatorio; el repo sólo incluye datos sintéticos propios; datos reales se importan por el operador con licencia válida |
| R4 | **Paper trading sin feed real**: sin proveedor, el "paper" sería un replay | Producto/confianza | `feed_kind` explícito, insignia `SIMULATED FEED`; decidir proveedor (pregunta Q1) |
| R5 | **Ejecución de código de usuario** si se adelanta sin sandbox | Crítico (RCE) | Fuera del MVP; sólo spec declarativo sin evaluación dinámica; diseño de sandbox en ADR-0002 |
| R6 | **Abuso de cómputo** (FREE lanzando backtests enormes) | Coste/disponibilidad | Entitlements, rate limit, límites de rango/símbolos por plan, timeouts por job, colas separadas |
| R7 | **Fuga entre tenants** | Crítico (seguridad) | Filtro por workspace en repositorios, tests de aislamiento, IDs no secuenciales |
| R8 | **Zonas horarias y calendarios** (DST, festivos, medias sesiones) | Alto | UTC en BD, `exchange_calendars`, tests con fechas de DST y festivos |
| R9 | **Sobreajuste presentado como éxito** | Producto/ético | Diagnostics (`MANY_TRIALS`, `LOW_TRADE_COUNT`, `SHORT_SAMPLE`), disclaimers, comparación neutral |
| R10 | **Crecimiento de `market_data`/equity points** con intradía | Rendimiento | Particionado o TimescaleDB cuando llegue intradía; PK diseñada para ello |
| R11 | **Deriva de contrato frontend/backend** | Mantenibilidad | Cliente TS generado desde OpenAPI; CI falla si el cliente no está regenerado |
| R12 | **Reproducibilidad rota** por cambios del motor | Confianza | `engine_version` + `config_hash` + `dataset_hash` en el experimento; `result_hash` para comprobar re-ejecuciones; golden tests |
| R13 | **Regulación**: presentar resultados como asesoramiento o rentabilidad esperada | Legal | Disclaimers, sin rankings de "mejor estrategia", sin live trading en MVP |

## 2. Decisiones difíciles de cambiar después

Cada una tiene un ADR con alternativas y consecuencias.

| Decisión | Elección propuesta | ADR |
|---|---|---|
| Motor como librería pura, independiente de backend | Sí, con reglas de import verificadas en CI | [0001](adr/0001-monorepo-and-pure-engine.md) |
| Representación de estrategias | Spec declarativo versionado e inmutable; protocolo Python para internas y sandbox futuro | [0002](adr/0002-strategy-representation.md) |
| Representación de dinero | `Decimal` en ledger, `float64` en analítica, `NUMERIC` en BD | [0003](adr/0003-money-representation.md) |
| Semántica temporal | `ts` = cierre de barra UTC; órdenes ejecutadas en el open siguiente | [0004](adr/0004-bar-timestamps-and-execution-timing.md) |
| Precios almacenados | Sin ajustar + corporate actions; ajuste *as-of* en el motor | [0005](adr/0005-raw-prices-plus-corporate-actions.md) |
| Cola de trabajos | Dramatiq + Redis detrás de `JobQueue`; estado en Postgres | [0006](adr/0006-job-queue.md) |
| Autenticación | Sesiones opacas en cookie HttpOnly, propias | [0007](adr/0007-auth-sessions.md) |
| Tenancy | Todo recurso pertenece a un workspace desde el día 1 | [0008](adr/0008-workspace-tenancy.md) |
| Arquitectura del motor | Event-driven (barra a barra), no vectorizado | [0009](adr/0009-event-driven-engine.md) |

## 3. Preguntas abiertas para el product owner

| # | Pregunta | Propuesta por defecto |
|---|---|---|
| Q1 | ¿Qué fuente de datos **reales** usaremos (dev y paper trading)? Opciones: CSV importados manualmente (p. ej. Stooq, uso personal), Tiingo, Polygon, Alpaca (datos + futuro broker) | Empezar con CSV importado por el operador con manifiesto; evaluar Alpaca para paper (datos + ruta natural a live) |
| Q2 | ¿Mercado inicial? | Acciones/ETFs EE. UU., diario |
| Q3 | Idioma de la UI y la documentación | Documentación en español, código e identificadores en inglés, UI en inglés con i18n preparado |
| Q4 | ¿Verificación de email obligatoria para usar el producto? | Obligatoria antes de lanzar backtests (anti-abuso); flag configurable |
| Q5 | Límites FREE adicionales (rango máximo, nº de paper accounts) | `backtests_per_day=5`, `paper_accounts=1`, rango ilimitado en diario |
