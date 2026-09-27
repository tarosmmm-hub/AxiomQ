# ADR-0004 — Timestamps de barra y momento de ejecución

**Contexto.** La causa más común de backtests falsamente buenos es usar información antes de que
exista. La convención temporal afecta a datos, motor, paper trading y UI.

**Decisión.** `ts` de una barra = instante de **cierre** (UTC), es decir, cuando su información está
disponible; se guarda también `session_date`. La estrategia en la barra `i` sólo ve barras con
`ts ≤ ts_i`. Las órdenes emitidas en `i` se ejecutan con el `FillModel` por defecto
`NextBarOpen` (open de `i+1`). No hay fill al close de la barra de señal en el MVP.

**Alternativas.** Timestamp de apertura (convención de muchos proveedores; se convierte en la
ingesta); fill al close (optimista salvo que el cálculo termine antes del cierre real).

**Consecuencias.** Los proveedores con timestamps de apertura se normalizan en el import. Añadir
fills intrabarra o MOC en el futuro es un `FillModel` nuevo, no un cambio de convención.
