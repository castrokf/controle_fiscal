from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user

from app.audit import record_audit
from app.auth.forms import LoginForm
from app.extensions import db
from app.models import User

bp = Blueprint("auth", __name__, url_prefix="/auth")


@bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.index"))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.lower().strip()).first()
        if user and user.is_active and user.check_password(form.password.data):
            login_user(user, remember=form.remember.data)
            record_audit("auth.login", entity_type="user", entity_id=user.id, status="OK", message="Login realizado.")
            db.session.commit()
            next_url = request.args.get("next")
            return redirect(next_url or url_for("dashboard.index"))

        record_audit("auth.login", entity_type="user", status="ERRO", message=f"Tentativa falhou para {form.email.data}.")
        db.session.commit()
        flash("Email ou senha invalidos.", "danger")

    return render_template("auth/login.html", form=form)


@bp.post("/logout")
@login_required
def logout():
    record_audit("auth.logout", entity_type="user", entity_id=current_user.id, status="OK", message="Logout realizado.")
    db.session.commit()
    logout_user()
    flash("Sessao encerrada.", "info")
    return redirect(url_for("auth.login"))
