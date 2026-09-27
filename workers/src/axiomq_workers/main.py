"""Worker entrypoint: ``dramatiq axiomq_workers.main``.

Importing this module configures the broker and registers every actor.
"""

from axiomq_api.core.config import get_settings
from axiomq_api.core.logging import configure_logging
from axiomq_workers.actors import system as _system  # noqa: F401

_settings = get_settings()
configure_logging(_settings.log_level, json_output=_settings.log_json)
