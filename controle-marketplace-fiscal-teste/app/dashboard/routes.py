from datetime import date, datetime, time
from decimal import Decimal

from flask import Blueprint, render_template
from flask_login import login_required
from sqlalchemy import or_

from app.models import (
    FISCAL_AUTORIZADA,
    FISCAL_REJEITADA,
    FISCAL_SEM_NFE,
    MARKETPLACE_AMAZON,
    MARKETPLACE_SHOPEE,
    MarketplaceOrder,
    Product,
)

bp = Blueprint("dashboard", __name__, url_prefix="/dashboard")


@bp.get("/")
@login_required
def index():
    today_start = datetime.combine(date.today(), time.min)
    today_end = datetime.combine(date.today(), time.max)
    today_orders = MarketplaceOrder.query.filter(
        MarketplaceOrder.order_datetime.between(today_start, today_end)
    ).all()

    amazon_today = sum(1 for order in today_orders if order.marketplace == MARKETPLACE_AMAZON)
    shopee_today = sum(1 for order in today_orders if order.marketplace == MARKETPLACE_SHOPEE)
    revenue_today = sum((order.total_amount for order in today_orders), Decimal("0.00"))
    revenue_by_marketplace = {
        MARKETPLACE_AMAZON: sum((order.total_amount for order in today_orders if order.marketplace == MARKETPLACE_AMAZON), Decimal("0.00")),
        MARKETPLACE_SHOPEE: sum((order.total_amount for order in today_orders if order.marketplace == MARKETPLACE_SHOPEE), Decimal("0.00")),
    }

    stats = {
        "orders_today": len(today_orders),
        "amazon_today": amazon_today,
        "shopee_today": shopee_today,
        "pending_invoices": MarketplaceOrder.query.filter_by(fiscal_status=FISCAL_SEM_NFE).count(),
        "authorized_invoices": MarketplaceOrder.query.filter_by(fiscal_status=FISCAL_AUTORIZADA).count(),
        "rejected_invoices": MarketplaceOrder.query.filter_by(fiscal_status=FISCAL_REJEITADA).count(),
        "products_without_ncm": Product.query.filter(or_(Product.ncm.is_(None), Product.ncm == "")).count(),
        "products_without_cfop": Product.query.filter(or_(Product.cfop.is_(None), Product.cfop == "")).count(),
        "revenue_today": revenue_today,
        "revenue_by_marketplace": revenue_by_marketplace,
    }

    recent_orders = (
        MarketplaceOrder.query.order_by(MarketplaceOrder.order_datetime.desc())
        .limit(12)
        .all()
    )
    return render_template("dashboard/index.html", stats=stats, recent_orders=recent_orders)
