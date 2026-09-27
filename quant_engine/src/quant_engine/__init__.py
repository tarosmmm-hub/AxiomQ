"""AxiomQ quantitative engine.

Pure, deterministic library: given a backtest configuration and market data it produces results.
It must never import the backend, the database layer, the web framework or the job queue
(enforced by import-linter, see the root pyproject.toml).

Phase 1 only ships the package skeleton; data, strategy, execution, portfolio, risk and metrics
modules arrive in Phases 2-5 (see docs/IMPLEMENTATION_PLAN.md).
"""

__version__ = "0.1.0"
ENGINE_VERSION = __version__

__all__ = ["ENGINE_VERSION", "__version__"]
