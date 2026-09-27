# data/

Datasets versionados en el repositorio. **Regla**: todo dataset va acompañado de un manifiesto
con `source`, `license`, `data_kind` (`REAL_HISTORICAL` | `SYNTHETIC`), `adjusted`, `timezone`,
`retrieved_at` y `sha256` (ver ARCHITECTURE §6).

- `fixtures/`: series pequeñas para tests. Sólo datos sintéticos generados por scripts
  deterministas y etiquetados `SYNTHETIC`. Nunca se presentan como datos de mercado reales.

No se incluyen datos reales de mercado en el repositorio (licencias). Los datos reales de EE. UU.
y de la Bolsa de Santiago se importan con el `HistoricalCSVProvider` y su manifiesto (Fase 2).
