import random
from datetime import date, datetime, time, timedelta
from decimal import Decimal

from app.audit import record_audit
from app.extensions import db
from app.models import (
    FISCAL_AUTORIZADA,
    FISCAL_DADOS_INCOMPLETOS,
    FISCAL_REJEITADA,
    FISCAL_SEM_NFE,
    MARKETPLACE_AMAZON,
    MARKETPLACE_SHOPEE,
    ORDER_STATUS_PAID,
    ORDER_STATUS_PENDING,
    ORDER_STATUS_SHIPPED,
    Address,
    AuditLog,
    Buyer,
    DailyClosing,
    Invoice,
    InvoiceEvent,
    MarketplaceOrder,
    OrderItem,
    Product,
    SystemSetting,
    User,
)
from app.fiscal.validators import validate_order

PRODUCT_NAMES = [
    "Cabo USB Ficticio",
    "Suporte de Mesa Simulado",
    "Mouse Sem Fio Demo",
    "Teclado Compacto Teste",
    "Garrafa Termica Ficticia",
    "Organizador de Cabos Demo",
    "Lampada LED Simulada",
    "Caderno Executivo Teste",
    "Carregador Portatil Fake",
    "Fone Bluetooth Simulado",
    "Case Protetora Ficticia",
    "Webcam Empresarial Demo",
    "Hub USB Teste",
    "Mochila Office Ficticia",
    "Etiqueta Termica Demo",
    "Caneta Touch Simulada",
    "Base Notebook Teste",
    "Adaptador HDMI Ficticio",
    "Mini Tripé Demo",
    "Calculadora Office Teste",
]

ORDER_STATUSES = [ORDER_STATUS_PAID, ORDER_STATUS_PENDING, ORDER_STATUS_SHIPPED]
MARKETPLACES = [MARKETPLACE_AMAZON, MARKETPLACE_SHOPEE]


def seed_database(reset=True):
    random.seed(20260528)
    db.create_all()
    if reset:
        _clear_database()

    admin = _create_admin_user()
    products = _create_products()
    orders = []
    for marketplace in MARKETPLACES:
        for index in range(1, 51):
            orders.append(_create_order(index=index, marketplace=marketplace, products=products))

    db.session.flush()
    invoices = _create_invoices_for_orders(orders, admin.id)
    _create_daily_closings()
    _create_settings()

    record_audit(
        "seed.executed",
        entity_type="database",
        status="OK",
        message="Banco populado com dados 100% ficticios para ambiente de teste.",
        user_id=admin.id,
    )
    db.session.commit()

    return {
        "users": User.query.count(),
        "products": Product.query.count(),
        "orders": MarketplaceOrder.query.count(),
        "invoices": len(invoices),
        "daily_closings": DailyClosing.query.count(),
    }


def generate_fake_orders(count=5, source="manual", user_id=None):
    products = Product.query.filter_by(is_active=True).all()
    if not products:
        products = _create_products()
        db.session.flush()

    orders = []
    for index in range(count):
        marketplace = random.choice(MARKETPLACES)
        order = _create_order(
            index=random.randint(1000, 9999) + index,
            marketplace=marketplace,
            products=products,
            created_now=True,
        )
        orders.append(order)

    record_audit(
        "fake_orders.generated",
        entity_type="marketplace_order",
        status="OK",
        message=f"{count} pedidos ficticios gerados via {source}.",
        user_id=user_id,
    )
    db.session.commit()
    return orders


def _clear_database():
    for model in [
        InvoiceEvent,
        Invoice,
        OrderItem,
        MarketplaceOrder,
        Address,
        Buyer,
        Product,
        DailyClosing,
        SystemSetting,
        AuditLog,
        User,
    ]:
        db.session.query(model).delete()
    db.session.commit()


def _create_admin_user():
    admin = User(name="Administrador Teste", email="admin@teste.com", role="admin", is_active=True)
    admin.set_password("Teste@1234")
    db.session.add(admin)
    db.session.flush()
    return admin


def _create_products():
    products = []
    for index, name in enumerate(PRODUCT_NAMES, start=1):
        product = Product(
            sku=f"SKU-FICT-{index:03d}",
            marketplace_sku=f"MKP-FICT-{index:03d}",
            name=name,
            ean=f"7890000000{index:03d}",
            ncm=None if index in {4, 9, 14, 19} else f"{84000000 + index}",
            cfop=None if index in {5, 10, 15, 20} else random.choice(["5102", "6102", "5405"]),
            cest="" if index % 6 else f"28.000.{index:02d}",
            unit="UN",
            origin=random.choice(["0", "1", "2"]),
            cst=random.choice(["00", "20", "40"]),
            csosn=random.choice(["101", "102", "500"]),
            cost_price=_money(12 + index * 1.7),
            sale_price=_money(29 + index * 3.1),
            is_active=True,
        )
        db.session.add(product)
        products.append(product)
    db.session.flush()
    return products


def _create_order(index, marketplace, products, created_now=False):
    buyer = _create_buyer(index=index, marketplace=marketplace)
    order_datetime = datetime.combine(date.today(), _time_for_order(index, marketplace))
    if not created_now and index > 35:
        order_datetime = order_datetime - timedelta(days=random.randint(1, 6))
    if created_now:
        order_datetime = datetime.now().replace(microsecond=0)

    selected_products = random.sample(products, k=random.randint(1, 3))
    subtotal = Decimal("0.00")
    order = MarketplaceOrder(
        marketplace=marketplace,
        marketplace_order_id=_order_number(marketplace, index),
        order_datetime=order_datetime,
        buyer=buyer,
        total_amount=Decimal("0.00"),
        shipping_amount=_money(random.choice([0, 9.9, 12.5, 18.9])),
        discount_amount=_money(random.choice([0, 3.5, 5.0, 7.9])),
        marketplace_fee=Decimal("0.00"),
        net_amount=Decimal("0.00"),
        order_status=random.choice(ORDER_STATUSES),
        fiscal_status=FISCAL_SEM_NFE,
        raw_payload_json={
            "ambiente": "teste_ficticio",
            "marketplace": marketplace,
            "observacao": "Payload simulado. Nenhuma API real foi chamada.",
        },
    )
    db.session.add(order)
    db.session.flush()

    for product in selected_products:
        quantity = random.randint(1, 4)
        unit_price = Decimal(product.sale_price)
        total_price = unit_price * quantity
        subtotal += total_price
        db.session.add(
            OrderItem(
                order=order,
                product=product,
                sku=product.sku,
                product_name=product.name,
                quantity=quantity,
                unit_price=unit_price,
                total_price=total_price,
                ncm=product.ncm,
                cfop=product.cfop,
                cest=product.cest,
                unit=product.unit,
            )
        )

    order.total_amount = subtotal
    order.marketplace_fee = _money(subtotal * Decimal("0.12"))
    order.net_amount = order.total_amount + order.shipping_amount - order.discount_amount - order.marketplace_fee
    return order


def _create_buyer(index, marketplace):
    safe_marketplace = marketplace.upper()[:3]
    buyer = Buyer(
        name=f"Cliente Ficticio {safe_marketplace} {index:03d}",
        document=f"FICT-DOC-{safe_marketplace}-{index:04d}",
        email=f"cliente{safe_marketplace.lower()}{index:03d}@exemplo.test",
        phone=f"0000-000-{index:04d}",
    )
    db.session.add(buyer)
    db.session.flush()
    db.session.add(
        Address(
            buyer=buyer,
            street=f"Rua Ficticia {index}",
            number=str(100 + index),
            complement="Sala Teste" if index % 4 == 0 else "",
            neighborhood="Bairro Simulado",
            city="Cidade Teste",
            state=random.choice(["SP", "RJ", "MG", "PR", "SC"]),
            zip_code=f"00000-{index % 1000:03d}",
            country="Brasil",
        )
    )
    return buyer


def _create_invoices_for_orders(orders, admin_id):
    invoices = []
    for position, order in enumerate(orders, start=1):
        errors = validate_order(order)
        if position % 3 == 0 and not errors:
            invoice = Invoice(
                order=order,
                invoice_number=f"{100000 + position}",
                invoice_series="TST",
                access_key=f"FAKE-ACCESS-KEY-{position:036d}",
                status=FISCAL_AUTORIZADA,
                issued_at=order.order_datetime + timedelta(minutes=12),
            )
            order.fiscal_status = FISCAL_AUTORIZADA
            db.session.add(invoice)
            db.session.flush()
            db.session.add(
                InvoiceEvent(
                    invoice=invoice,
                    event_type="authorized",
                    message="NF-e ficticia autorizada no ambiente de teste.",
                    payload_json={"fake": True},
                )
            )
            invoices.append(invoice)
        elif position % 5 == 0:
            reason = "; ".join(errors) if errors else "Rejeicao simulada para testar fluxo operacional."
            invoice = Invoice(
                order=order,
                invoice_number=f"REJ-{position:05d}",
                invoice_series="TST",
                access_key=f"FAKE-REJECTED-KEY-{position:032d}",
                status=FISCAL_REJEITADA,
                rejection_reason=reason,
                issued_at=order.order_datetime + timedelta(minutes=8),
            )
            order.fiscal_status = FISCAL_REJEITADA
            db.session.add(invoice)
            db.session.flush()
            db.session.add(
                InvoiceEvent(
                    invoice=invoice,
                    event_type="rejected",
                    message=reason,
                    payload_json={"fake": True, "errors": errors},
                )
            )
            invoices.append(invoice)
        elif errors:
            order.fiscal_status = FISCAL_DADOS_INCOMPLETOS

    record_audit(
        "fake_invoices.seeded",
        entity_type="invoice",
        status="OK",
        message="Notas fiscais ficticias autorizadas e rejeitadas criadas no seed.",
        user_id=admin_id,
    )
    return invoices


def _create_daily_closings():
    for days_back in range(0, 7):
        closing_date = date.today() - timedelta(days=days_back)
        for marketplace in MARKETPLACES:
            orders = MarketplaceOrder.query.filter(
                MarketplaceOrder.marketplace == marketplace,
                MarketplaceOrder.order_datetime >= datetime.combine(closing_date, time.min),
                MarketplaceOrder.order_datetime <= datetime.combine(closing_date, time.max),
            ).all()
            if not orders:
                continue
            closing = DailyClosing(
                date=closing_date,
                marketplace=marketplace,
                orders_count=len(orders),
                gross_revenue=sum((order.total_amount for order in orders), Decimal("0.00")),
                shipping_total=sum((order.shipping_amount for order in orders), Decimal("0.00")),
                discounts_total=sum((order.discount_amount for order in orders), Decimal("0.00")),
                marketplace_fees_total=sum((order.marketplace_fee for order in orders), Decimal("0.00")),
                net_revenue=sum((order.net_amount for order in orders), Decimal("0.00")),
                invoices_pending=sum(1 for order in orders if order.fiscal_status == FISCAL_SEM_NFE),
                invoices_authorized=sum(1 for order in orders if order.fiscal_status == FISCAL_AUTORIZADA),
                invoices_rejected=sum(1 for order in orders if order.fiscal_status == FISCAL_REJEITADA),
            )
            db.session.add(closing)


def _create_settings():
    settings = {
        "AUTO_GENERATE_FAKE_ORDERS": "false",
        "FAKE_ORDER_INTERVAL_MINUTES": "10",
        "ENVIRONMENT_NOTICE": "Ambiente 100% ficticio. Nao emite NF-e real.",
    }
    for key, value in settings.items():
        db.session.add(SystemSetting(key=key, value=value))


def _order_number(marketplace, index):
    prefix = "AMZ" if marketplace == MARKETPLACE_AMAZON else "SHP"
    suffix = random.randint(1000, 9999)
    return f"{prefix}-TESTE-{index:04d}-{suffix}"


def _time_for_order(index, marketplace):
    if marketplace == MARKETPLACE_SHOPEE and index <= 18:
        return time(hour=index % 6, minute=(index * 7) % 60)
    if marketplace == MARKETPLACE_AMAZON and index <= 10:
        return time(hour=(index + 6) % 24, minute=(index * 5) % 60)
    return time(hour=random.randint(7, 23), minute=random.randint(0, 59))


def _money(value):
    return Decimal(str(value)).quantize(Decimal("0.01"))
