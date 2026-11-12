from typing import Any

import structlog

from app.shared.security import Principal

_log = structlog.get_logger("audit")


def audit_admin(actor: Principal, action: str, **details: Any) -> None:
    """Structured audit trail for admin actions (shipped with the app logs)."""
    _log.info(
        "admin_action",
        action=action,
        actor_id=str(actor.user_id),
        actor_roles=sorted(actor.roles),
        **details,
    )
