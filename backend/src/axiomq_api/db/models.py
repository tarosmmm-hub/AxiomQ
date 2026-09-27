"""Import every model module so that ``Base.metadata`` is complete (Alembic, tests)."""

from axiomq_api.db.base import Base
from axiomq_api.modules.analytics import models as _analytics  # noqa: F401
from axiomq_api.modules.audit import models as _audit  # noqa: F401
from axiomq_api.modules.billing import models as _billing  # noqa: F401
from axiomq_api.modules.identity import models as _identity  # noqa: F401
from axiomq_api.modules.workspaces import models as _workspaces  # noqa: F401

__all__ = ["Base"]
