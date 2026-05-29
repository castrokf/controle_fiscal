from datetime import datetime, time

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import login_required
from sqlalchemy import Time, cast, or_

from app.extensions import db
from app.fiscal.nfe_service import NFeService
from app.models import AuditLog, Buyer, MarketplaceOrder, OrderItem
from app.security import roles_required

bp = Blueprint("orders", __name__, url_prefix="/orders")

DEFAULT_TIME_START = time.min.strftime("%H:%M")
DEFAULT_TIME_END = "23:59"


@bp.get("/")
@login_required
def index():
    query = MarketplaceOrder.query.outerjoin(Buyer)

    marketplace = request.args.get("marketplace", "").strip()
    date_start = request.args.get("date_start", "").strip()
    date_end = request.args.get("date_end", "").strip()
    time_start = request.args.get("time_start", "").strip()
    time_end = request.args.get("time_end", "").strip()
    order_status = request.args.get("order_status", "").strip()
    fiscal_status = request.args.get("fiscal_status", "").strip()
    sku = request.args.get("sku", "").strip()
    buyer = request.args.get("buyer", "").strip()
    order_number = request.args.get("order_number", "").strip()

    if marketplace:
        query = query.filter(MarketplaceOrder.marketplace == marketplace)
    if date_start:
        query = query.filter(MarketplaceOrder.order_datetime >= _parse_datetime(date_start, time_start or DEFAULT_TIME_START))
    if date_end:
        query = query.filter(MarketplaceOrder.order_datetime <= _parse_datetime(date_end, time_end or DEFAULT_TIME_END))
    if time_start or time_end:
        query = _apply_time_filter(query, time_start or DEFAULT_TIME_START, time_end or DEFAULT_TIME_END)
    if order_status:
        query = query.filter(MarketplaceOrder.order_status == order_status)
    if fiscal_status:
        query = query.filter(MarketplaceOrder.fiscal_status == fiscal_status)
    if buyer:
        query = query.filter(Buyer.name.ilike(f"%{buyer}%"))
    if order_number:
        query = query.filter(MarketplaceOrder.marketplace_order_id.ilike(f"%{order_number}%"))
    if sku:
        query = query.join(OrderItem).filter(OrderItem.sku.ilike(f"%{sku}%")).distinct()

    orders = query.order_by(MarketplaceOrder.order_datetime.desc()).limit(300).all()
    return render_template("orders/index.html", orders=orders, filters=request.args)


@bp.get("/<int:order_id>")
@login_required
def detail(order_id):
    order = db.get_or_404(MarketplaceOrder, order_id)
    log_filters = [((AuditLog.entity_type == "marketplace_order") & (AuditLog.entity_id == order.id))]
    if order.invoice:
        log_filters.append((AuditLog.entity_type == "invoice") & (AuditLog.entity_id == order.invoice.id))
    logs = AuditLog.query.filter(or_(*log_filters)).order_by(AuditLog.created_at.desc()).limit(30).all()
    return render_template("orders/detail.html", order=order, logs=logs)


@bp.post("/<int:order_id>/validate")
@login_required
@roles_required("admin", "operador")
def validate(order_id):
    order = db.get_or_404(MarketplaceOrder, order_id)
    errors = NFeService().validate_order(order)
    if errors:
        flash("Validacao fiscal simulada encontrou pendencias.", "danger")
    else:
        flash("Operacao pronta para emissao simulada.", "success")
    return redirect(url_for("orders.detail", order_id=order.id))


@bp.post("/<int:order_id>/issue")
@login_required
@roles_required("admin", "operador")
def issue(order_id):
    order = db.get_or_404(MarketplaceOrder, order_id)
    invoice = NFeService().issue_fake_invoice(order)
    if "AUTORIZADA" in invoice.status:
        flash("NF-e simulada autorizada no ambiente demo.", "success")
    else:
        flash("NF-e simulada rejeitada no ambiente demo.", "danger")
    return redirect(url_for("orders.detail", order_id=order.id))


@bp.post("/<int:order_id>/generate-files")
@login_required
@roles_required("admin", "operador")
def generate_files(order_id):
    order = db.get_or_404(MarketplaceOrder, order_id)
    if not order.invoice:
        flash("Emita uma NF-e simulada antes de gerar XML/PDF.", "warning")
        return redirect(url_for("orders.detail", order_id=order.id))
    NFeService().generate_fake_files(order.invoice)
    flash("XML e PDF gerados com sucesso.", "success")
    return redirect(url_for("orders.detail", order_id=order.id))


def _parse_datetime(date_value, time_value):
    return datetime.strptime(f"{date_value} {time_value}", "%Y-%m-%d %H:%M")


def _apply_time_filter(query, start_value, end_value):
    bind = query.session.get_bind()
    if bind.dialect.name == "sqlite":
        from sqlalchemy import func

        time_expr = func.strftime("%H:%M", MarketplaceOrder.order_datetime)
        if start_value <= end_value:
            return query.filter(time_expr >= start_value, time_expr <= end_value)
        return query.filter(or_(time_expr >= start_value, time_expr <= end_value))

    start_time = time.fromisoformat(start_value)
    end_time = time.fromisoformat(end_value)
    time_expr = cast(MarketplaceOrder.order_datetime, Time)
    if start_time <= end_time:
        return query.filter(time_expr >= start_time, time_expr <= end_time)
    return query.filter(or_(time_expr >= start_time, time_expr <= end_time))
