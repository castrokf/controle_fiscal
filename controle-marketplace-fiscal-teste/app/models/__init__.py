from datetime import UTC, datetime

from flask_login import UserMixin

from app.extensions import bcrypt, db


def utcnow():
    return datetime.now(UTC).replace(tzinfo=None)

ROLE_ADMIN = "admin"
ROLE_OPERATOR = "operador"
ROLE_READONLY = "leitura"

MARKETPLACE_AMAZON = "Amazon"
MARKETPLACE_SHOPEE = "Shopee"

ORDER_STATUS_PENDING = "PENDENTE"
ORDER_STATUS_PAID = "PAGO"
ORDER_STATUS_SHIPPED = "ENVIADO"
ORDER_STATUS_CANCELLED = "CANCELADO"

FISCAL_SEM_NFE = "SEM_NFE"
FISCAL_DADOS_INCOMPLETOS = "DADOS_INCOMPLETOS"
FISCAL_PRONTO = "PRONTO_PARA_EMITIR"
FISCAL_EMITINDO = "EMITINDO_NFE"
FISCAL_AUTORIZADA = "NFE_FICTICIA_AUTORIZADA"
FISCAL_REJEITADA = "NFE_FICTICIA_REJEITADA"
FISCAL_XML_GERADO = "XML_FAKE_GERADO"
FISCAL_PDF_GERADO = "PDF_FAKE_GERADO"


class TimestampMixin:
    created_at = db.Column(db.DateTime, default=utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=utcnow, onupdate=utcnow, nullable=False)


class User(UserMixin, TimestampMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(30), nullable=False, default=ROLE_OPERATOR)
    is_active = db.Column(db.Boolean, default=True, nullable=False)

    audit_logs = db.relationship("AuditLog", back_populates="user", lazy=True)

    def set_password(self, password):
        self.password_hash = bcrypt.generate_password_hash(password).decode("utf-8")

    def check_password(self, password):
        return bcrypt.check_password_hash(self.password_hash, password)


class Product(TimestampMixin, db.Model):
    __tablename__ = "products"

    id = db.Column(db.Integer, primary_key=True)
    sku = db.Column(db.String(80), unique=True, nullable=False, index=True)
    marketplace_sku = db.Column(db.String(120), nullable=True)
    name = db.Column(db.String(255), nullable=False)
    ean = db.Column(db.String(40), nullable=True)
    ncm = db.Column(db.String(20), nullable=True)
    cfop = db.Column(db.String(20), nullable=True)
    cest = db.Column(db.String(20), nullable=True)
    unit = db.Column(db.String(10), nullable=False, default="UN")
    origin = db.Column(db.String(10), nullable=True)
    cst = db.Column(db.String(10), nullable=True)
    csosn = db.Column(db.String(10), nullable=True)
    cost_price = db.Column(db.Numeric(12, 2), nullable=False, default=0)
    sale_price = db.Column(db.Numeric(12, 2), nullable=False, default=0)
    is_active = db.Column(db.Boolean, default=True, nullable=False)

    order_items = db.relationship("OrderItem", back_populates="product", lazy=True)

    @property
    def has_fiscal_gaps(self):
        return not self.ncm or not self.cfop


class Buyer(TimestampMixin, db.Model):
    __tablename__ = "buyers"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(160), nullable=False)
    document = db.Column(db.String(40), nullable=True)
    email = db.Column(db.String(255), nullable=True)
    phone = db.Column(db.String(40), nullable=True)

    addresses = db.relationship("Address", back_populates="buyer", cascade="all, delete-orphan", lazy=True)
    orders = db.relationship("MarketplaceOrder", back_populates="buyer", lazy=True)


class Address(TimestampMixin, db.Model):
    __tablename__ = "addresses"

    id = db.Column(db.Integer, primary_key=True)
    buyer_id = db.Column(db.Integer, db.ForeignKey("buyers.id"), nullable=False, index=True)
    street = db.Column(db.String(160), nullable=False)
    number = db.Column(db.String(30), nullable=False)
    complement = db.Column(db.String(120), nullable=True)
    neighborhood = db.Column(db.String(120), nullable=False)
    city = db.Column(db.String(120), nullable=False)
    state = db.Column(db.String(2), nullable=False)
    zip_code = db.Column(db.String(20), nullable=False)
    country = db.Column(db.String(80), nullable=False, default="Brasil")

    buyer = db.relationship("Buyer", back_populates="addresses")


class MarketplaceOrder(TimestampMixin, db.Model):
    __tablename__ = "marketplace_orders"

    id = db.Column(db.Integer, primary_key=True)
    marketplace = db.Column(db.String(40), nullable=False, index=True)
    marketplace_order_id = db.Column(db.String(80), unique=True, nullable=False, index=True)
    order_datetime = db.Column(db.DateTime, nullable=False, index=True)
    buyer_id = db.Column(db.Integer, db.ForeignKey("buyers.id"), nullable=True, index=True)
    total_amount = db.Column(db.Numeric(12, 2), nullable=False, default=0)
    shipping_amount = db.Column(db.Numeric(12, 2), nullable=False, default=0)
    discount_amount = db.Column(db.Numeric(12, 2), nullable=False, default=0)
    marketplace_fee = db.Column(db.Numeric(12, 2), nullable=False, default=0)
    net_amount = db.Column(db.Numeric(12, 2), nullable=False, default=0)
    order_status = db.Column(db.String(40), nullable=False, default=ORDER_STATUS_PENDING, index=True)
    fiscal_status = db.Column(db.String(60), nullable=False, default=FISCAL_SEM_NFE, index=True)
    raw_payload_json = db.Column(db.JSON, nullable=True)

    buyer = db.relationship("Buyer", back_populates="orders")
    items = db.relationship("OrderItem", back_populates="order", cascade="all, delete-orphan", lazy=True)
    invoice = db.relationship("Invoice", back_populates="order", uselist=False, cascade="all, delete-orphan")


class OrderItem(db.Model):
    __tablename__ = "order_items"

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey("marketplace_orders.id"), nullable=False, index=True)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=True, index=True)
    sku = db.Column(db.String(80), nullable=False)
    product_name = db.Column(db.String(255), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=1)
    unit_price = db.Column(db.Numeric(12, 2), nullable=False, default=0)
    total_price = db.Column(db.Numeric(12, 2), nullable=False, default=0)
    ncm = db.Column(db.String(20), nullable=True)
    cfop = db.Column(db.String(20), nullable=True)
    cest = db.Column(db.String(20), nullable=True)
    unit = db.Column(db.String(10), nullable=False, default="UN")
    created_at = db.Column(db.DateTime, default=utcnow, nullable=False)

    order = db.relationship("MarketplaceOrder", back_populates="items")
    product = db.relationship("Product", back_populates="order_items")


class Invoice(TimestampMixin, db.Model):
    __tablename__ = "invoices"

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey("marketplace_orders.id"), unique=True, nullable=False, index=True)
    invoice_number = db.Column(db.String(30), nullable=True)
    invoice_series = db.Column(db.String(20), nullable=True)
    access_key = db.Column(db.String(80), nullable=True)
    xml_path = db.Column(db.String(255), nullable=True)
    pdf_path = db.Column(db.String(255), nullable=True)
    status = db.Column(db.String(60), nullable=False, default=FISCAL_SEM_NFE, index=True)
    rejection_reason = db.Column(db.Text, nullable=True)
    issued_at = db.Column(db.DateTime, nullable=True)

    order = db.relationship("MarketplaceOrder", back_populates="invoice")
    events = db.relationship("InvoiceEvent", back_populates="invoice", cascade="all, delete-orphan", lazy=True)


class InvoiceEvent(db.Model):
    __tablename__ = "invoice_events"

    id = db.Column(db.Integer, primary_key=True)
    invoice_id = db.Column(db.Integer, db.ForeignKey("invoices.id"), nullable=False, index=True)
    event_type = db.Column(db.String(80), nullable=False)
    message = db.Column(db.Text, nullable=False)
    payload_json = db.Column(db.JSON, nullable=True)
    created_at = db.Column(db.DateTime, default=utcnow, nullable=False)

    invoice = db.relationship("Invoice", back_populates="events")


class AuditLog(db.Model):
    __tablename__ = "audit_logs"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True, index=True)
    action = db.Column(db.String(120), nullable=False, index=True)
    entity_type = db.Column(db.String(80), nullable=True, index=True)
    entity_id = db.Column(db.Integer, nullable=True, index=True)
    status = db.Column(db.String(30), nullable=False, default="OK", index=True)
    message = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=utcnow, nullable=False, index=True)

    user = db.relationship("User", back_populates="audit_logs")


class DailyClosing(db.Model):
    __tablename__ = "daily_closings"

    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False, index=True)
    marketplace = db.Column(db.String(40), nullable=False, index=True)
    orders_count = db.Column(db.Integer, nullable=False, default=0)
    gross_revenue = db.Column(db.Numeric(12, 2), nullable=False, default=0)
    shipping_total = db.Column(db.Numeric(12, 2), nullable=False, default=0)
    discounts_total = db.Column(db.Numeric(12, 2), nullable=False, default=0)
    marketplace_fees_total = db.Column(db.Numeric(12, 2), nullable=False, default=0)
    net_revenue = db.Column(db.Numeric(12, 2), nullable=False, default=0)
    invoices_pending = db.Column(db.Integer, nullable=False, default=0)
    invoices_authorized = db.Column(db.Integer, nullable=False, default=0)
    invoices_rejected = db.Column(db.Integer, nullable=False, default=0)
    created_at = db.Column(db.DateTime, default=utcnow, nullable=False)

    __table_args__ = (db.UniqueConstraint("date", "marketplace", name="uq_daily_closing_date_marketplace"),)


class SystemSetting(TimestampMixin, db.Model):
    __tablename__ = "system_settings"

    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(120), unique=True, nullable=False, index=True)
    value = db.Column(db.Text, nullable=True)
