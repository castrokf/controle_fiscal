from flask import Blueprint, flash, redirect, render_template, url_for
from flask_login import current_user, login_required

from app.fake_data import generate_fake_orders
from app.models import SystemSetting
from app.security import roles_required

bp = Blueprint("settings", __name__, url_prefix="/settings")


@bp.get("/")
@login_required
def index():
    settings = SystemSetting.query.order_by(SystemSetting.key.asc()).all()
    return render_template("settings/index.html", settings=settings)


@bp.post("/generate-fake-orders")
@login_required
@roles_required("admin", "operador")
def generate_fake_orders_now():
    generate_fake_orders(count=5, source="manual_button", user_id=current_user.id)
    flash("5 pedidos ficticios foram gerados.", "success")
    return redirect(url_for("orders.index"))
