"""Actor modules. Importing this package configures the broker first, so every actor binds to
the AxiomQ broker regardless of import order."""

from axiomq_workers import broker as _broker  # noqa: F401
