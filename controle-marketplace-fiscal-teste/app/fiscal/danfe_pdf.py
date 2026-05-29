from io import BytesIO
from textwrap import wrap

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

from app.models import utcnow


def build_fake_danfe_pdf(invoice):
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4, pageCompression=0)
    width, height = A4
    order = invoice.order
    buyer = order.buyer
    address = buyer.addresses[0] if buyer and buyer.addresses else None

    pdf.setTitle("Nota fiscal simulada - ambiente demo")
    pdf.setAuthor("Controle Fiscal - Ambiente Demo")
    _draw_page_frame(pdf, width, height)
    _draw_receipt_strip(pdf, width, height, invoice)
    _draw_header(pdf, width, height, invoice)
    _draw_protocol(pdf, width, height, invoice)
    _draw_recipient(pdf, width, height, buyer, address, invoice)
    _draw_values(pdf, width, height, order)
    _draw_transport(pdf, width, height)
    _draw_items(pdf, width, height, order)
    _draw_additional_info(pdf, width, height, invoice)
    _draw_footer(pdf, width)

    pdf.showPage()
    pdf.save()
    return buffer.getvalue()


def _draw_page_frame(pdf, width, height):
    pdf.setLineWidth(0.6)
    pdf.rect(18, 18, width - 36, height - 36)
    _text(pdf, 24, height - 28, "NOTA FISCAL FICTICIA - MODELO VISUAL PARA TESTE", 8, bold=True)


def _draw_receipt_strip(pdf, width, height, invoice):
    y = height - 44
    _box(pdf, 24, y - 36, width - 48, 36)
    _text(pdf, 28, y - 11, "RECEBEMOS OS PRODUTOS FICTICIOS CONSTANTES DA NOTA FISCAL SIMULADA ABAIXO", 7)
    _text(pdf, 28, y - 24, "FINALIDADE: testar download, conferencia e arquivamento. DOCUMENTO SEM VALIDADE FISCAL.", 7, bold=True)
    _box(pdf, width - 150, y - 36, 126, 36)
    _text(pdf, width - 145, y - 12, f"NF-e FICTICIA No {invoice.invoice_number or '-'}", 8, bold=True)
    _text(pdf, width - 145, y - 25, f"SERIE {invoice.invoice_series or '-'}", 8)


def _draw_header(pdf, width, height, invoice):
    order = invoice.order
    y = height - 90
    left_w = 330
    right_x = 365
    right_w = width - right_x - 24

    _box(pdf, 24, y - 92, left_w, 92, "EMITENTE FICTICIO")
    _text(pdf, 30, y - 22, "CONTROLE FISCAL - AMBIENTE DEMO", 9, bold=True)
    _text(pdf, 30, y - 37, "Rua Ficticia do Sistema, 100 - Cidade Teste/BR", 8)
    _text(pdf, 30, y - 52, "CNPJ simulado: 00.000.000/0000-00", 8)
    _text(pdf, 30, y - 67, "Nao representa empresa real. Nenhuma API fiscal real foi chamada.", 7)

    _box(pdf, right_x, y - 92, right_w, 92)
    _text(pdf, right_x + 8, y - 17, "DANFE FICTICIO", 13, bold=True)
    _text(pdf, right_x + 8, y - 34, "DOCUMENTO AUXILIAR DE NOTA FISCAL ELETRONICA", 6)
    _text(pdf, right_x + 8, y - 49, "0 - ENTRADA     1 - SAIDA", 8)
    _box(pdf, right_x + 104, y - 58, 18, 18)
    _text(pdf, right_x + 110, y - 53, "1", 10, bold=True)
    _text(pdf, right_x + 8, y - 69, f"No {invoice.invoice_number or '-'}", 8, bold=True)
    _text(pdf, right_x + 8, y - 82, f"SERIE {invoice.invoice_series or '-'}     FOLHA 1/1", 8)

    y2 = y - 102
    _box(pdf, 24, y2 - 30, left_w, 30, "NATUREZA DA OPERACAO")
    _text(pdf, 30, y2 - 21, "VENDA FICTICIA PARA SIMULACAO DE MARKETPLACE", 8)

    _box(pdf, right_x, y2 - 30, right_w, 30, "CHAVE DE ACESSO FICTICIA")
    _text(pdf, right_x + 8, y2 - 21, invoice.access_key or "-", 7, bold=True)

    y3 = y2 - 40
    _box(pdf, 24, y3 - 30, 160, 30, "INSCRICAO ESTADUAL")
    _text(pdf, 30, y3 - 21, "ISENTO - TESTE", 8)
    _box(pdf, 184, y3 - 30, 170, 30, "CNPJ FICTICIO")
    _text(pdf, 190, y3 - 21, "00.000.000/0000-00", 8)
    _box(pdf, right_x, y3 - 30, right_w, 30, "PEDIDO MARKETPLACE")
    _text(pdf, right_x + 8, y3 - 21, f"{order.marketplace} / {order.marketplace_order_id}", 7)


def _draw_protocol(pdf, width, height, invoice):
    y = height - 265
    _box(pdf, 24, y - 28, width - 48, 28, "PROTOCOLO DE AUTORIZACAO DE USO FICTICIO")
    _text(
        pdf,
        30,
        y - 19,
        f"Status simulado: {invoice.status} | Gerado em {utcnow().strftime('%d/%m/%Y %H:%M:%S')} | Nao enviado para SEFAZ",
        8,
    )


def _draw_recipient(pdf, width, height, buyer, address, invoice):
    y = height - 305
    _section_title(pdf, 24, y + 9, "DESTINATARIO / REMETENTE FICTICIO")
    _box(pdf, 24, y - 28, 280, 28, "NOME / RAZAO SOCIAL")
    _text(pdf, 30, y - 19, buyer.name if buyer else "-", 8)
    _box(pdf, 304, y - 28, 150, 28, "DOCUMENTO FICTICIO")
    _text(pdf, 310, y - 19, buyer.document if buyer else "-", 8)
    _box(pdf, 454, y - 28, width - 478, 28, "DATA DA EMISSAO")
    _text(pdf, 460, y - 19, invoice.issued_at.strftime("%d/%m/%Y") if invoice.issued_at else "-", 8)

    y2 = y - 28
    _box(pdf, 24, y2 - 28, 260, 28, "ENDERECO")
    _text(pdf, 30, y2 - 19, _address_street(address), 8)
    _box(pdf, 284, y2 - 28, 110, 28, "BAIRRO")
    _text(pdf, 290, y2 - 19, address.neighborhood if address else "-", 8)
    _box(pdf, 394, y2 - 28, 90, 28, "CEP")
    _text(pdf, 400, y2 - 19, address.zip_code if address else "-", 8)
    _box(pdf, 484, y2 - 28, width - 508, 28, "UF")
    _text(pdf, 490, y2 - 19, address.state if address else "-", 8)

    y3 = y2 - 28
    _box(pdf, 24, y3 - 28, 210, 28, "MUNICIPIO")
    _text(pdf, 30, y3 - 19, address.city if address else "-", 8)
    _box(pdf, 234, y3 - 28, 170, 28, "EMAIL")
    _text(pdf, 240, y3 - 19, buyer.email if buyer else "-", 7)
    _box(pdf, 404, y3 - 28, 100, 28, "FONE")
    _text(pdf, 410, y3 - 19, buyer.phone if buyer else "-", 8)
    _box(pdf, 504, y3 - 28, width - 528, 28, "DATA SAIDA")
    _text(pdf, 510, y3 - 19, "-", 8)


def _draw_values(pdf, width, height, order):
    y = height - 418
    _section_title(pdf, 24, y + 9, "CALCULO DO IMPOSTO FICTICIO")
    labels = [
        ("BASE CALCULO", "0,00"),
        ("VALOR IMPOSTO", "0,00"),
        ("FRETE", _br_money(order.shipping_amount)),
        ("DESCONTO", _br_money(order.discount_amount)),
        ("TAXAS", _br_money(order.marketplace_fee)),
        ("VALOR TOTAL", _br_money(order.total_amount)),
    ]
    x = 24
    w = (width - 48) / len(labels)
    for title, value in labels:
        _box(pdf, x, y - 34, w, 34, title)
        _text(pdf, x + 5, y - 23, value, 8, bold=True)
        x += w


def _draw_transport(pdf, width, height):
    y = height - 470
    _section_title(pdf, 24, y + 9, "TRANSPORTADOR / VOLUMES TRANSPORTADOS - FICTICIO")
    _box(pdf, 24, y - 28, 220, 28, "RAZAO SOCIAL")
    _text(pdf, 30, y - 19, "Transportadora simulada", 8)
    _box(pdf, 244, y - 28, 105, 28, "FRETE POR CONTA")
    _text(pdf, 250, y - 19, "0 - Emitente", 8)
    _box(pdf, 349, y - 28, 80, 28, "QUANTIDADE")
    _text(pdf, 355, y - 19, "1", 8)
    _box(pdf, 429, y - 28, 80, 28, "ESPECIE")
    _text(pdf, 435, y - 19, "VOLUME", 8)
    _box(pdf, 509, y - 28, width - 533, 28, "PESO")
    _text(pdf, 515, y - 19, "0,000", 8)


def _draw_items(pdf, width, height, order):
    y = height - 522
    _section_title(pdf, 24, y + 9, "DADOS DOS PRODUTOS / SERVICOS FICTICIOS")
    _box(pdf, 24, y - 24, width - 48, 24)
    columns = [
        (28, "SKU"),
        (82, "DESCRICAO"),
        (282, "CLASS. FISCAL"),
        (358, "COD. OPERACAO"),
        (438, "QTD"),
        (482, "VLR UNIT."),
        (532, "TOTAL"),
    ]
    for x, label in columns:
        _text(pdf, x, y - 16, label, 6, bold=True)

    row_y = y - 24
    for item in order.items[:7]:
        _box(pdf, 24, row_y - 24, width - 48, 24)
        _text(pdf, 28, row_y - 15, item.sku, 6)
        _text(pdf, 82, row_y - 15, _truncate(item.product_name, 38), 6)
        _text(pdf, 282, row_y - 15, item.ncm or "PENDENTE", 6)
        _text(pdf, 358, row_y - 15, item.cfop or "PENDENTE", 6)
        _text(pdf, 438, row_y - 15, str(item.quantity), 6)
        _text(pdf, 482, row_y - 15, _br_money(item.unit_price), 6)
        _text(pdf, 532, row_y - 15, _br_money(item.total_price), 6)
        row_y -= 24
    if len(order.items) > 7:
        _text(pdf, 28, row_y - 15, f"Mais {len(order.items) - 7} item(ns) simulado(s) omitido(s) nesta visualizacao.", 7)


def _draw_additional_info(pdf, width, height, invoice):
    order = invoice.order
    y = 172
    _section_title(pdf, 24, y + 9, "DADOS ADICIONAIS / CORPO DA SIMULACAO")
    _box(pdf, 24, 56, width - 48, 116)
    lines = [
        "FINALIDADE: validar o fluxo de download, conferencia, armazenamento e auditoria de notas fiscais simuladas.",
        "AVISO: documento sem validade fiscal, nao enviado para SEFAZ, sem certificado digital e sem emissao real.",
        f"Origem: {order.marketplace}. Operacao simulada: {order.marketplace_order_id}.",
        f"Receita liquida simulada: {_br_money(order.net_amount)}.",
    ]
    if invoice.rejection_reason:
        lines.append(f"Motivo de rejeicao simulada: {invoice.rejection_reason}")
    body_lines = []
    for line in lines:
        body_lines.extend(wrap(line, width=96, break_long_words=False))
    text_y = 158
    for line in body_lines[:6]:
        _text(pdf, 30, text_y, line, 7)
        text_y -= 14


def _draw_footer(pdf, width):
    _text(pdf, 24, 36, "CONTROLE FISCAL - AMBIENTE DEMO | PDF simulado gerado localmente.", 7)
    _text(pdf, 24, 25, "Nao usar como documento fiscal real. Nenhum dado real deve ser inserido neste ambiente.", 7, bold=True)


def _section_title(pdf, x, y, title):
    _text(pdf, x, y, title, 7, bold=True)


def _box(pdf, x, y, w, h, title=None):
    pdf.setLineWidth(0.45)
    pdf.rect(x, y, w, h)
    if title:
        _text(pdf, x + 4, y + h - 8, title, 5.8, bold=True)


def _text(pdf, x, y, text, size=8, bold=False):
    pdf.setFont("Helvetica-Bold" if bold else "Helvetica", size)
    pdf.drawString(x, y, str(text or ""))


def _truncate(value, limit):
    value = str(value or "")
    if len(value) <= limit:
        return value
    return value[: limit - 3] + "..."


def _address_street(address):
    if not address:
        return "-"
    return f"{address.street}, {address.number}"


def _br_money(value):
    value = float(value or 0)
    return f"{value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
