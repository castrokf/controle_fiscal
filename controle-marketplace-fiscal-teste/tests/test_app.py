from pathlib import Path

from app.cli import _initial_admin_config_error
from app.config import _database_url
from app.extensions import db
from app.models import FISCAL_AUTORIZADA, FISCAL_PRONTO, MarketplaceOrder, Product, User
from app.security import reset_login_failures
from tests.conftest import create_complete_order, create_user, login


def test_protected_route_requires_login(client):
    response = client.get("/dashboard/")
    assert response.status_code == 302
    assert "/auth/login" in response.headers["Location"]


def test_login_with_seed_admin_credentials(client, app):
    with app.app_context():
        create_user()
    response = login(client)
    assert response.status_code == 200
    assert b"Painel fiscal" in response.data


def test_login_page_does_not_expose_demo_credentials(client):
    response = client.get("/auth/login")
    assert response.status_code == 200
    assert b"admin@teste.com" not in response.data
    assert b"Teste@1234" not in response.data
    assert b"SenhaQa@123456789" not in response.data


def test_login_rejects_external_next_redirect(client, app):
    with app.app_context():
        create_user()
    response = client.post(
        "/auth/login?next=https://example.com/phishing",
        data={"email": "usuario.qa@example.com", "password": "SenhaQa@123456789"},
        follow_redirects=False,
    )
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/dashboard/")


def test_login_rate_limit_blocks_repeated_failures(client):
    reset_login_failures()
    for _ in range(3):
        response = client.post(
            "/auth/login",
            data={"email": "bloqueio@example.com", "password": "senha-errada"},
        )
        assert response.status_code == 200

    response = client.post(
        "/auth/login",
        data={"email": "bloqueio@example.com", "password": "senha-errada"},
    )
    assert response.status_code == 429
    reset_login_failures()


def test_security_headers_are_applied(client):
    response = client.get("/auth/login")
    assert response.headers["X-Frame-Options"] == "DENY"
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert "frame-ancestors 'none'" in response.headers["Content-Security-Policy"]


def test_database_url_accepts_render_postgres_scheme(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgres://user:pass@host:5432/dbname")
    assert _database_url() == "postgresql+psycopg2://user:pass@host:5432/dbname"


def test_initial_admin_config_validation(app):
    with app.app_context():
        app.config["INITIAL_ADMIN_EMAIL"] = ""
        app.config["INITIAL_ADMIN_PASSWORD"] = ""
        assert "INITIAL_ADMIN_EMAIL" in _initial_admin_config_error()

        app.config["INITIAL_ADMIN_EMAIL"] = "email-invalido"
        app.config["INITIAL_ADMIN_PASSWORD"] = "SenhaForte@2026"
        assert "email valido" in _initial_admin_config_error()

        app.config["INITIAL_ADMIN_EMAIL"] = "usuario.qa@example.com"
        app.config["INITIAL_ADMIN_PASSWORD"] = "curta"
        assert "politica de senha" in _initial_admin_config_error()

        app.config["INITIAL_ADMIN_PASSWORD"] = "SenhaForte@2026"
        assert _initial_admin_config_error() is None


def test_create_product(client, app):
    with app.app_context():
        create_user()
    login(client)
    response = client.post(
        "/products/create",
        data={
            "sku": "SKU-NOVO-001",
            "marketplace_sku": "MKP-NOVO-001",
            "name": "Produto Novo Ficticio",
            "ean": "7890000001111",
            "ncm": "84000000",
            "cfop": "5102",
            "cest": "",
            "unit": "UN",
            "origin": "0",
            "cst": "00",
            "csosn": "102",
            "cost_price": "10.00",
            "sale_price": "39.90",
            "is_active": "y",
        },
        follow_redirects=True,
    )
    assert response.status_code == 200
    with app.app_context():
        assert Product.query.filter_by(sku="SKU-NOVO-001").count() == 1


def test_seed_creates_fake_data(app):
    runner = app.test_cli_runner()
    result = runner.invoke(args=["seed"])
    assert result.exit_code == 0
    with app.app_context():
        assert User.query.filter_by(email=app.config["INITIAL_ADMIN_EMAIL"]).count() == 1
        assert Product.query.count() == 20
        assert MarketplaceOrder.query.count() == 100


def test_orders_list_and_time_filter(client, app):
    runner = app.test_cli_runner()
    assert runner.invoke(args=["seed"]).exit_code == 0
    login(client)
    response = client.get("/orders/?marketplace=Shopee&time_start=08:00&time_end=23:59")
    assert response.status_code == 200
    assert b"Shopee" in response.data
    assert b"SHP-TESTE" in response.data


def test_validate_issue_and_generate_fake_files(client, app):
    with app.app_context():
        create_user()
        order = create_complete_order()
        order_id = order.id

    login(client)
    response = client.post(f"/orders/{order_id}/validate", follow_redirects=True)
    assert response.status_code == 200
    with app.app_context():
        order = db.session.get(MarketplaceOrder, order_id)
        assert order.fiscal_status == FISCAL_PRONTO

    response = client.post(f"/orders/{order_id}/issue", follow_redirects=True)
    assert response.status_code == 200
    with app.app_context():
        order = db.session.get(MarketplaceOrder, order_id)
        assert order.invoice is not None
        assert order.invoice.status == FISCAL_AUTORIZADA
        invoice_id = order.invoice.id

    response = client.post(f"/orders/{order_id}/generate-files", follow_redirects=True)
    assert response.status_code == 200
    with app.app_context():
        order = db.session.get(MarketplaceOrder, order_id)
        xml_path = Path(app.config["STORAGE_DIR"]) / order.invoice.xml_path
        pdf_path = Path(app.config["STORAGE_DIR"]) / order.invoice.pdf_path
        assert xml_path.exists()
        assert pdf_path.exists()

    response = client.get(f"/fiscal/invoices/{invoice_id}/download/xml")
    assert response.status_code == 200
    assert response.mimetype == "application/xml"
    assert b"<finalidade>" in response.data
    assert b"<corpo>" in response.data
    assert b"Documento gerado para demonstrar" in response.data

    with app.app_context():
        local_download_dir = Path(app.config["STORAGE_DIR"]).parent / "local-downloads-test"
        app.config["LOCAL_DOWNLOAD_COPY_ENABLED"] = True
        app.config["LOCAL_DOWNLOAD_DIR"] = str(local_download_dir)
        response = client.get(f"/fiscal/invoices/{invoice_id}/download/pdf")
        assert response.status_code == 200
        assert b"FINALIDADE" in response.data
        assert b"CORPO DA SIMULACAO" in response.data
        assert (local_download_dir / "nfe-fake-1.pdf").exists()


def test_reports_and_csv_export(client, app):
    runner = app.test_cli_runner()
    assert runner.invoke(args=["seed"]).exit_code == 0
    login(client)
    response = client.get("/reports/")
    assert response.status_code == 200
    assert b"Operacoes por origem" in response.data
    response = client.get("/reports/export/orders.csv")
    assert response.status_code == 200
    assert response.mimetype == "text/csv"
