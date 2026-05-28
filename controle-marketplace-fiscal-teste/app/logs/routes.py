from flask import Blueprint, render_template, request
from flask_login import login_required

from app.models import AuditLog

bp = Blueprint("logs", __name__, url_prefix="/logs")


@bp.get("/")
@login_required
def index():
    query = AuditLog.query
    action = request.args.get("action", "").strip()
    status = request.args.get("status", "").strip()
    entity_type = request.args.get("entity_type", "").strip()
    if action:
        query = query.filter(AuditLog.action.ilike(f"%{action}%"))
    if status:
        query = query.filter(AuditLog.status == status)
    if entity_type:
        query = query.filter(AuditLog.entity_type == entity_type)
    logs = query.order_by(AuditLog.created_at.desc()).limit(300).all()
    return render_template("logs/index.html", logs=logs)
