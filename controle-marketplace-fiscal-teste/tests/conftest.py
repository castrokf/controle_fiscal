from datetime import datetime
from decimal import Decimal

import pytest

from app import create_app
from app.extensions import db
from app.models import Address, Buyer, MarketplaceOrder, OrderItem, Product, User


@pytest.fixture()
def app(tmp_path):
    test_app = create_app(
        "testing",
        {
            "STORAGE_DIR": str(tmp_path / "storage"),
            "WTF_CSRF_ENABLED": False,
        },
    )
    with test_app.app_context():
        db.create_all()
        yield test_app
        db.session.remove()
        db.drop_all()


@pytest.fixture()
def client(app):
    return app.test_client()


def create_user(email="admin@teste.com", password="SenhaTeste@123456", role="admin"):
    user = User(name="Admin Teste", email=email, role=role, is_active=True)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    return user


def login(client, email="admin@teste.com", password="SenhaTeste@123456"):
    return client.post(
        "/auth/login",
        data={"email": email, "password": password},
        follow_redirects=True,
    )


def create_complete_order():
    product = Product(
        sku="SKU-TESTE-OK",
        marketplace_sku="MKP-TESTE-OK",
        name="Produto Fiscal Completo",
        ean="7890000000000",
        ncm="84000000",
        cfop="5102",
        unit="UN",
        origin="0",
        cst="00",
        csosn="102",
        cost_price=Decimal("10.00"),
        sale_price=Decimal("25.00"),
        is_active=True,
    )
    buyer = Buyer(
        name="Cliente Ficticio Teste",
        document="FICT-DOC-TESTE-0001",
        email="cliente.teste@exemplo.test",
        phone="0000-000-0001",
    )
    db.session.add_all([product, buyer])
    db.session.flush()
    db.session.add(
        Address(
            buyer=buyer,
            street="Rua Ficticia Teste",
            number="100",
            neighborhood="Bairro Teste",
            city="Cidade Teste",
            state="SP",
            zip_code="00000-001",
            country="Brasil",
        )
    )
    order = MarketplaceOrder(
        marketplace="Shopee",
        marketplace_order_id="SHP-TESTE-FISCAL-0001",
        order_datetime=datetime(2026, 5, 28, 1, 30),
        buyer=buyer,
        total_amount=Decimal("25.00"),
        shipping_amount=Decimal("0.00"),
        discount_amount=Decimal("0.00"),
        marketplace_fee=Decimal("2.50"),
        net_amount=Decimal("22.50"),
        order_status="PAGO",
        fiscal_status="SEM_NFE",
        raw_payload_json={"fake": True},
    )
    db.session.add(order)
    db.session.flush()
    db.session.add(
        OrderItem(
            order=order,
            product=product,
            sku=product.sku,
            product_name=product.name,
            quantity=1,
            unit_price=Decimal("25.00"),
            total_price=Decimal("25.00"),
            ncm=product.ncm,
            cfop=product.cfop,
            unit="UN",
        )
    )
    db.session.commit()
    return order
