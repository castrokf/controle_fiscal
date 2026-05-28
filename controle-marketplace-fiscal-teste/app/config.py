import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent


def _database_url():
    value = os.getenv("DATABASE_URL")
    if not value:
        return f"sqlite:///{BASE_DIR / 'storage' / 'app.db'}"
    if value.startswith("sqlite:///"):
        raw_path = value.replace("sqlite:///", "", 1)
        path = Path(raw_path)
        if not path.is_absolute():
            return f"sqlite:///{BASE_DIR / path}"
    return value


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-me")
    SQLALCHEMY_DATABASE_URI = _database_url()
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    WTF_CSRF_TIME_LIMIT = None
    STORAGE_DIR = os.getenv("STORAGE_DIR", str(BASE_DIR / "storage"))
    LOCAL_DOWNLOAD_COPY_ENABLED = os.getenv("LOCAL_DOWNLOAD_COPY_ENABLED", "true").lower() == "true"
    LOCAL_DOWNLOAD_DIR = os.getenv(
        "LOCAL_DOWNLOAD_DIR",
        str(Path.home() / "Downloads" / "controle-marketplace-fiscal-teste"),
    )
    FAKE_INVOICE_TEMPLATE_PDF = os.getenv("FAKE_INVOICE_TEMPLATE_PDF", "")
    AUTO_GENERATE_FAKE_ORDERS = os.getenv("AUTO_GENERATE_FAKE_ORDERS", "false").lower() == "true"
    FAKE_ORDER_INTERVAL_MINUTES = int(os.getenv("FAKE_ORDER_INTERVAL_MINUTES", "10"))
    DEBUG = False
    TESTING = False


class DevelopmentConfig(Config):
    DEBUG = True


class TestingConfig(Config):
    TESTING = True
    WTF_CSRF_ENABLED = False
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    AUTO_GENERATE_FAKE_ORDERS = False
    LOCAL_DOWNLOAD_COPY_ENABLED = False


class ProductionConfig(Config):
    DEBUG = False


config_by_name = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig,
}
