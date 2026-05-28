from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import login_required
from sqlalchemy import or_

from app.audit import record_audit
from app.extensions import db
from app.models import Product
from app.products.forms import ProductForm
from app.security import roles_required

bp = Blueprint("products", __name__, url_prefix="/products")


@bp.get("/")
@login_required
def index():
    q = request.args.get("q", "").strip()
    fiscal_gap = request.args.get("fiscal_gap")
    query = Product.query
    if q:
        query = query.filter(or_(Product.sku.ilike(f"%{q}%"), Product.name.ilike(f"%{q}%")))
    if fiscal_gap == "ncm":
        query = query.filter(or_(Product.ncm.is_(None), Product.ncm == ""))
    if fiscal_gap == "cfop":
        query = query.filter(or_(Product.cfop.is_(None), Product.cfop == ""))
    products = query.order_by(Product.name.asc()).all()
    return render_template("products/index.html", products=products)


@bp.route("/create", methods=["GET", "POST"])
@login_required
@roles_required("admin", "operador")
def create():
    form = ProductForm()
    if form.validate_on_submit():
        if Product.query.filter_by(sku=form.sku.data.strip()).first():
            flash("Ja existe um produto com este SKU.", "danger")
            return render_template("products/form.html", form=form, product=None)
        product = Product()
        _fill_product(product, form)
        db.session.add(product)
        db.session.flush()
        record_audit("product.created", "product", product.id, "OK", f"Produto {product.sku} criado.")
        db.session.commit()
        flash("Produto cadastrado com sucesso.", "success")
        return redirect(url_for("products.index"))
    return render_template("products/form.html", form=form, product=None)


@bp.route("/<int:product_id>/edit", methods=["GET", "POST"])
@login_required
@roles_required("admin", "operador")
def edit(product_id):
    product = db.get_or_404(Product, product_id)
    form = ProductForm(obj=product)
    if form.validate_on_submit():
        existing = Product.query.filter(Product.sku == form.sku.data.strip(), Product.id != product.id).first()
        if existing:
            flash("Ja existe outro produto com este SKU.", "danger")
            return render_template("products/form.html", form=form, product=product)
        _fill_product(product, form)
        record_audit("product.updated", "product", product.id, "OK", f"Produto {product.sku} atualizado.")
        db.session.commit()
        flash("Produto atualizado com sucesso.", "success")
        return redirect(url_for("products.index"))
    return render_template("products/form.html", form=form, product=product)


def _fill_product(product, form):
    product.sku = form.sku.data.strip()
    product.marketplace_sku = (form.marketplace_sku.data or "").strip()
    product.name = form.name.data.strip()
    product.ean = (form.ean.data or "").strip()
    product.ncm = (form.ncm.data or "").strip()
    product.cfop = (form.cfop.data or "").strip()
    product.cest = (form.cest.data or "").strip()
    product.unit = form.unit.data
    product.origin = form.origin.data
    product.cst = (form.cst.data or "").strip()
    product.csosn = (form.csosn.data or "").strip()
    product.cost_price = form.cost_price.data or 0
    product.sale_price = form.sale_price.data or 0
    product.is_active = bool(form.is_active.data)
