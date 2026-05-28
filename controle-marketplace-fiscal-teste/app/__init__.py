import os
from pathlib import Path

from flask import Flask, redirect, render_template, url_for
from flask_login import current_user

from app.config import config_by_name
from app.extensions import bcrypt, csrf, db, login_manager, migrate
from app.utils import date_br, datetime_br, mask_document, mask_email, mask_phone, money_br, status_class, status_label


def create_app(config_name=None, config_overrides=None):
    app = Flask(__name__)
    selected_config = config_name or os.getenv("FLASK_ENV", "default")
    app.config.from_object(config_by_name.get(selected_config, config_by_name["default"]))
    if config_overrides:
        app.config.update(config_overrides)

    _ensure_storage_dirs(app)
    _init_extensions(app)
    _register_blueprints(app)
    _register_cli(app)
    _register_template_helpers(app)
    _register_error_handlers(app)
    _maybe_start_scheduler(app)

    @app.get("/")
    def index():
        if current_user.is_authenticated:
            return redirect(url_for("dashboard.index"))
        return redirect(url_for("auth.login"))

    return app


def _init_extensions(app):
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf.init_app(app)
    bcrypt.init_app(app)

    login_manager.login_view = "auth.login"
    login_manager.login_message = "Faça login para acessar esta área."
    login_manager.login_message_category = "warning"

    from app.models import User

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))


def _register_blueprints(app):
    from app.auth.routes import bp as auth_bp
    from app.closing.routes import bp as closing_bp
    from app.dashboard.routes import bp as dashboard_bp
    from app.fiscal.routes import bp as fiscal_bp
    from app.logs.routes import bp as logs_bp
    from app.orders.routes import bp as orders_bp
    from app.products.routes import bp as products_bp
    from app.reports.routes import bp as reports_bp
    from app.settings.routes import bp as settings_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(orders_bp)
    app.register_blueprint(products_bp)
    app.register_blueprint(fiscal_bp)
    app.register_blueprint(reports_bp)
    app.register_blueprint(closing_bp)
    app.register_blueprint(logs_bp)
    app.register_blueprint(settings_bp)


def _register_cli(app):
    from app.cli import seed_command

    app.cli.add_command(seed_command)


def _register_template_helpers(app):
    app.jinja_env.filters["money_br"] = money_br
    app.jinja_env.filters["datetime_br"] = datetime_br
    app.jinja_env.filters["date_br"] = date_br
    app.jinja_env.filters["mask_document"] = mask_document
    app.jinja_env.filters["mask_email"] = mask_email
    app.jinja_env.filters["mask_phone"] = mask_phone
    app.jinja_env.filters["status_class"] = status_class
    app.jinja_env.filters["status_label"] = status_label


def _register_error_handlers(app):
    @app.errorhandler(403)
    def forbidden(error):
        return render_template("errors/403.html"), 403

    @app.errorhandler(404)
    def not_found(error):
        return render_template("errors/404.html"), 404


def _ensure_storage_dirs(app):
    storage_dir = Path(app.config["STORAGE_DIR"])
    (storage_dir / "invoices" / "xml").mkdir(parents=True, exist_ok=True)
    (storage_dir / "invoices" / "pdf").mkdir(parents=True, exist_ok=True)


def _maybe_start_scheduler(app):
    if app.config.get("TESTING") or not app.config.get("AUTO_GENERATE_FAKE_ORDERS"):
        return

    from apscheduler.schedulers.background import BackgroundScheduler

    from app.fake_data import generate_fake_orders

    scheduler = BackgroundScheduler(daemon=True)

    def job():
        with app.app_context():
            generate_fake_orders(count=3, source="scheduler")

    scheduler.add_job(
        job,
        "interval",
        minutes=app.config.get("FAKE_ORDER_INTERVAL_MINUTES", 10),
        id="generate_fake_orders",
        replace_existing=True,
    )
    scheduler.start()
