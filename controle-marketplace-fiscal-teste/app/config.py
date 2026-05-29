import os
from datetime import timedelta
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent


def _env_bool(name, default="false"):
    return os.getenv(name, default).strip().lower() in {"1", "true", "yes", "on"}


def _env_int(name, default):
    value = os.getenv(name, str(default)).strip()
    try:
        return int(value)
    except ValueError as exc:
        raise RuntimeError(f"{name} precisa ser um numero inteiro.") from exc


def _secret_key():
    value = os.getenv("SECRET_KEY")
    if value:
        return value
    if os.getenv("FLASK_ENV") == "production":
        raise RuntimeError("SECRET_KEY precisa estar definida em producao.")
    return "dev-secret-key-change-me"


def _database_url():
    value = os.getenv("DATABASE_URL")
    if not value:
        return f"sqlite:///{BASE_DIR / 'storage' / 'app.db'}"
    if value.startswith("postgres://"):
        return value.replace("postgres://", "postgresql+psycopg2://", 1)
    if value.startswith("sqlite:///"):
        raw_path = value.replace("sqlite:///", "", 1)
        path = Path(raw_path)
        if not path.is_absolute():
            return f"sqlite:///{BASE_DIR / path}"
    return value


class Config:
    SECRET_KEY = _secret_key()
    SQLALCHEMY_DATABASE_URI = _database_url()
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    WTF_CSRF_TIME_LIMIT = _env_int("WTF_CSRF_TIME_LIMIT_SECONDS", 3600)
    MAX_CONTENT_LENGTH = _env_int("MAX_CONTENT_LENGTH_BYTES", 5 * 1024 * 1024)
    BCRYPT_LOG_ROUNDS = _env_int("BCRYPT_LOG_ROUNDS", 12)
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = False
    REMEMBER_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_SAMESITE = "Lax"
    REMEMBER_COOKIE_SECURE = False
    PERMANENT_SESSION_LIFETIME = timedelta(hours=_env_int("SESSION_LIFETIME_HOURS", 8))
    REMEMBER_COOKIE_DURATION = timedelta(days=_env_int("REMEMBER_COOKIE_DAYS", 7))
    SESSION_REFRESH_EACH_REQUEST = True
    STORAGE_DIR = os.getenv("STORAGE_DIR", str(BASE_DIR / "storage"))
    LOCAL_DOWNLOAD_COPY_ENABLED = os.getenv("LOCAL_DOWNLOAD_COPY_ENABLED", "true").lower() == "true"
    LOCAL_DOWNLOAD_DIR = os.getenv(
        "LOCAL_DOWNLOAD_DIR",
        str(Path.home() / "Downloads" / "controle-marketplace-fiscal-teste"),
    )
    FAKE_INVOICE_TEMPLATE_PDF = os.getenv("FAKE_INVOICE_TEMPLATE_PDF", "")
    AUTO_GENERATE_FAKE_ORDERS = os.getenv("AUTO_GENERATE_FAKE_ORDERS", "false").lower() == "true"
    FAKE_ORDER_INTERVAL_MINUTES = int(os.getenv("FAKE_ORDER_INTERVAL_MINUTES", "10"))
    ENABLE_AUTO_SEED = _env_bool("ENABLE_AUTO_SEED", "false")
    INITIAL_ADMIN_NAME = os.getenv("INITIAL_ADMIN_NAME", "Administrador")
    INITIAL_ADMIN_EMAIL = os.getenv("INITIAL_ADMIN_EMAIL", "")
    INITIAL_ADMIN_PASSWORD = os.getenv("INITIAL_ADMIN_PASSWORD", "")
    LOGIN_MAX_ATTEMPTS = _env_int("LOGIN_MAX_ATTEMPTS", 5)
    LOGIN_ATTEMPT_WINDOW_SECONDS = _env_int("LOGIN_ATTEMPT_WINDOW_SECONDS", 300)
    LOGIN_LOCKOUT_SECONDS = _env_int("LOGIN_LOCKOUT_SECONDS", 900)
    SECURITY_HEADERS_ENABLED = _env_bool("SECURITY_HEADERS_ENABLED", "true")
    SECURITY_HSTS_ENABLED = _env_bool("SECURITY_HSTS_ENABLED", "false")
    TRUST_PROXY_HEADERS = _env_bool("TRUST_PROXY_HEADERS", "false")
    DEBUG = False
    TESTING = False


class DevelopmentConfig(Config):
    DEBUG = True


class TestingConfig(Config):
    TESTING = True
    WTF_CSRF_ENABLED = False
    WTF_CSRF_TIME_LIMIT = None
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    AUTO_GENERATE_FAKE_ORDERS = False
    LOCAL_DOWNLOAD_COPY_ENABLED = False
    BCRYPT_LOG_ROUNDS = 4
    INITIAL_ADMIN_EMAIL = "admin@teste.com"
    INITIAL_ADMIN_PASSWORD = "SenhaTeste@123456"
    LOGIN_MAX_ATTEMPTS = 3
    LOGIN_ATTEMPT_WINDOW_SECONDS = 60
    LOGIN_LOCKOUT_SECONDS = 120
    SECURITY_HSTS_ENABLED = False


class ProductionConfig(Config):
    DEBUG = False
    SESSION_COOKIE_SECURE = True
    REMEMBER_COOKIE_SECURE = True
    SECURITY_HSTS_ENABLED = True
    TRUST_PROXY_HEADERS = True
    PREFERRED_URL_SCHEME = "https"


config_by_name = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig,
}
