from flask import Blueprint, flash, redirect, render_template, request, session, url_for
from flask_login import current_user, login_required, login_user, logout_user

from app.audit import record_audit
from app.auth.forms import LoginForm
from app.extensions import db
from app.models import User
from app.security import (
    clear_login_failures,
    get_login_lock_remaining,
    is_safe_redirect_url,
    normalize_email,
    register_login_failure,
)
from app.utils import mask_email

bp = Blueprint("auth", __name__, url_prefix="/auth")


@bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.index"))

    form = LoginForm()
    if form.validate_on_submit():
        email = normalize_email(form.email.data)
        lock_remaining = get_login_lock_remaining(email)
        if lock_remaining:
            record_audit(
                "auth.login_blocked",
                entity_type="user",
                status="ERRO",
                message=f"Tentativas excessivas para {mask_email(email)}.",
            )
            db.session.commit()
            flash("Muitas tentativas de login. Aguarde alguns minutos e tente novamente.", "danger")
            return render_template("auth/login.html", form=form), 429

        user = User.query.filter_by(email=email).first()
        if user and user.is_active and user.check_password(form.password.data):
            clear_login_failures(email)
            session.clear()
            session.permanent = True
            login_user(user, remember=form.remember.data)
            record_audit("auth.login", entity_type="user", entity_id=user.id, status="OK", message="Login realizado.")
            db.session.commit()
            next_url = request.args.get("next")
            if is_safe_redirect_url(next_url):
                return redirect(next_url)
            return redirect(url_for("dashboard.index"))

        register_login_failure(email)
        record_audit(
            "auth.login",
            entity_type="user",
            status="ERRO",
            message=f"Tentativa falhou para {mask_email(email)}.",
        )
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
