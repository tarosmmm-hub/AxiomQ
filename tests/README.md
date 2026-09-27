# tests/

Pruebas que cruzan paquetes. Los tests unitarios y de integración de cada paquete viven junto a
él (`backend/tests`, `quant_engine/tests`, `workers/tests`).

- `e2e/`: Playwright contra el stack real (FastAPI + PostgreSQL + Next.js). `make test-e2e`.
  Si Playwright no puede descargar navegadores, apunta a uno local con
  `PLAYWRIGHT_CHROMIUM_EXECUTABLE=/ruta/a/chrome`.
- `integration/`: flujos API → cola → worker → motor (a partir de la Fase 4).
