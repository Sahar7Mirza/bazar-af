from sqlalchemy.orm import Session

from app.core.logging import request_id_var
from app.models import AuditLog


def record(
    db: Session,
    action: str,
    *,
    actor_id: int | None = None,
    entity_type: str | None = None,
    entity_id=None,
    detail: dict | None = None,
    ip: str | None = None,
):
    """Append an audit row in the caller's transaction. Never put passwords, tokens or full PII in `detail`."""
    rid = request_id_var.get()
    db.add(
        AuditLog(
            actor_id=actor_id,
            action=action,
            entity_type=entity_type,
            entity_id=str(entity_id) if entity_id is not None else None,
            detail=detail,
            ip=ip,
            request_id=None if rid == "-" else rid,
        )
    )
