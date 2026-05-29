from datetime import date, datetime, time
from io import StringIO

import pandas as pd
from flask import Blueprint, Response, render_template
from flask_login import login_required
from sqlalchemy import desc, extract, func, or_

from app.audit import record_audit
from app.extensions import db
from app.models import (
    FISCAL_AUTORIZADA,
    FISCAL_REJEITADA,
    FISCAL_SEM_NFE,
    MarketplaceOrder,
    OrderItem,
    Product,
)

bp = Blueprint("reports", __name__, url_prefix="/reports")


@bp.get("/")
@login_required
def index():
    today_start = datetime.combine(date.today(), time.min)
    today_end = datetime.combine(date.today(), time.max)

    by_marketplace = (
        db.session.query(
            MarketplaceOrder.marketplace,
            func.count(MarketplaceOrder.id),
            func.coalesce(func.sum(MarketplaceOrder.total_amount), 0),
        )
        .group_by(MarketplaceOrder.marketplace)
        .all()
    )
    by_hour = _orders_by_hour()
    daily_revenue = (
        db.session.query(func.coalesce(func.sum(MarketplaceOrder.total_amount), 0))
        .filter(MarketplaceOrder.order_datetime.between(today_start, today_end))
        .scalar()
    )
    top_products = (
        db.session.query(OrderItem.sku, OrderItem.product_name, func.sum(OrderItem.quantity).label("qty"))
        .group_by(OrderItem.sku, OrderItem.product_name)
        .order_by(desc("qty"))
        .limit(10)
        .all()
    )
    report = {
        "by_marketplace": by_marketplace,
        "by_hour": by_hour,
        "daily_revenue": daily_revenue,
        "pending_invoices": MarketplaceOrder.query.filter_by(fiscal_status=FISCAL_SEM_NFE).count(),
        "authorized_invoices": MarketplaceOrder.query.filter_by(fiscal_status=FISCAL_AUTORIZADA).count(),
        "rejected_invoices": MarketplaceOrder.query.filter_by(fiscal_status=FISCAL_REJEITADA).count(),
        "top_products": top_products,
        "products_without_ncm": Product.query.filter(or_(Product.ncm.is_(None), Product.ncm == "")).all(),
        "products_without_cfop": Product.query.filter(or_(Product.cfop.is_(None), Product.cfop == "")).all(),
    }
    record_audit("report.viewed", entity_type="report", status="OK", message="Tela de relatorios acessada.")
    db.session.commit()
    return render_template("reports/index.html", report=report)


@bp.get("/export/orders.csv")
@login_required
def export_orders_csv():
    orders = MarketplaceOrder.query.order_by(MarketplaceOrder.order_datetime.desc()).all()
    rows = [
        {
            "data_hora": order.order_datetime.isoformat(sep=" ", timespec="minutes"),
            "marketplace": order.marketplace,
            "pedido": order.marketplace_order_id,
            "cliente_ficticio": order.buyer.name if order.buyer else "",
            "valor_total": float(order.total_amount),
            "status_pedido": order.order_status,
            "status_fiscal": order.fiscal_status,
        }
        for order in orders
    ]
    output = StringIO()
    pd.DataFrame(rows).to_csv(output, index=False, sep=";")
    record_audit("report.export_csv", entity_type="report", status="OK", message="Exportacao CSV de pedidos gerada.")
    db.session.commit()
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=operacoes-fiscais-demo.csv"},
    )


def _orders_by_hour():
    bind = db.session.get_bind()
    if bind.dialect.name == "sqlite":
        rows = (
            db.session.query(
                func.strftime("%H", MarketplaceOrder.order_datetime).label("hour"),
                func.count(MarketplaceOrder.id),
            )
            .group_by("hour")
            .order_by("hour")
            .all()
        )
    else:
        rows = (
            db.session.query(
                extract("hour", MarketplaceOrder.order_datetime).label("hour"),
                func.count(MarketplaceOrder.id),
            )
            .group_by("hour")
            .order_by("hour")
            .all()
        )

    counts_by_hour = {int(hour): count for hour, count in rows}
    return [
        {
            "range": f"{hour:02d}:00 - {hour:02d}:59",
            "count": counts_by_hour.get(hour, 0),
        }
        for hour in range(24)
    ]
