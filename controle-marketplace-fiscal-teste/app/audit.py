from flask import has_request_context
from flask_login import current_user

from app.extensions import db
from app.models import AuditLog


def record_audit(action, entity_type=None, entity_id=None, status="OK", message="", user_id=None, commit=False):
    resolved_user_id = user_id
    if resolved_user_id is None and has_request_context() and current_user and current_user.is_authenticated:
        resolved_user_id = current_user.id

    log = AuditLog(
        user_id=resolved_user_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        status=status,
        message=message,
    )
    db.session.add(log)
    if commit:
        db.session.commit()
    return log
