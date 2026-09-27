# ADR-0009 — Motor event-driven

**Contexto.** Los motores vectorizados son rápidos pero facilitan el look-ahead (desplazamientos
olvidados), modelan mal la contabilidad con costes y sizing dependiente del cash, y no se pueden
reutilizar para paper trading.

**Decisión.** Motor event-driven barra a barra: el mismo pipeline (Strategy → Risk → Execution →
Portfolio) sirve para backtest y paper. Los indicadores se calculan de forma incremental o sobre
vistas truncadas.

**Consecuencias.** Más lento que un motor vectorizado; suficiente para barras diarias (decenas de
años × pocos activos en milisegundos-segundos). Para barridos de parámetros masivos se podrá añadir
un pre-filtro vectorizado cuyos candidatos se validan siempre con el motor event-driven.
