from decimal import Decimal

from flask_wtf import FlaskForm
from wtforms import BooleanField, DecimalField, SelectField, StringField, SubmitField
from wtforms.validators import DataRequired, Length, Optional


class ProductForm(FlaskForm):
    sku = StringField("SKU", validators=[DataRequired(), Length(max=80)])
    marketplace_sku = StringField("SKU marketplace", validators=[Optional(), Length(max=120)])
    name = StringField("Nome", validators=[DataRequired(), Length(max=255)])
    ean = StringField("Codigo de barras (EAN)", validators=[Optional(), Length(max=40)])
    ncm = StringField("Classificacao fiscal do produto (NCM)", validators=[Optional(), Length(max=20)])
    cfop = StringField("Codigo fiscal da operacao (CFOP)", validators=[Optional(), Length(max=20)])
    cest = StringField("Codigo CEST para substituicao tributaria", validators=[Optional(), Length(max=20)])
    unit = SelectField("Unidade", choices=[("UN", "UN"), ("CX", "CX"), ("KG", "KG"), ("PC", "PC")])
    origin = SelectField("Origem", choices=[("0", "0 - Nacional"), ("1", "1 - Estrangeira direta"), ("2", "2 - Estrangeira mercado interno")])
    cst = StringField("Codigo de situacao tributaria (CST)", validators=[Optional(), Length(max=10)])
    csosn = StringField("Codigo do Simples Nacional (CSOSN)", validators=[Optional(), Length(max=10)])
    cost_price = DecimalField("Preco de custo", places=2, default=Decimal("0.00"))
    sale_price = DecimalField("Preco de venda", places=2, default=Decimal("0.00"))
    is_active = BooleanField("Ativo", default=True)
    submit = SubmitField("Salvar")
