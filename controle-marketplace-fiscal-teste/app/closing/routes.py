from flask import Blueprint, render_template
from flask_login import login_required

from app.models import DailyClosing

bp = Blueprint("closing", __name__, url_prefix="/closing")


@bp.get("/")
@login_required
def index():
    closings = DailyClosing.query.order_by(DailyClosing.date.desc(), DailyClosing.marketplace.asc()).all()
    return render_template("closing/index.html", closings=closings)
