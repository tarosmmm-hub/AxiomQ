# ADR-0005 — Precios sin ajustar + corporate actions

**Contexto.** Las series back-adjusted usan información futura (splits/dividendos posteriores)
para reescribir precios pasados, distorsionan niveles absolutos (umbrales de precio, tamaño de
posición) y no son los precios negociables.

**Decisión.** Guardar precios sin ajustar y una tabla `corporate_actions`. El motor ejecuta a precio
sin ajustar, aplica splits a posiciones y abona dividendos en la ex-date, y ofrece a la estrategia
un histórico ajustado *as-of* `t`. Si un dataset sólo existe ajustado, se importa con
`adjusted = true` y se muestra un aviso.

**Consecuencias.** Más lógica en el motor (tests dedicados), a cambio de corrección y de poder
reproducir tanto el retorno de precio como el retorno total.
