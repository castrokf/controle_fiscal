import uuid
from pathlib import Path

from flask import current_app

from app.extensions import db
from app.fiscal.base import FiscalProvider
from app.fiscal.danfe_pdf import build_fake_danfe_pdf
from app.fiscal.validators import validate_order
from app.models import (
    FISCAL_AUTORIZADA,
    FISCAL_REJEITADA,
    Invoice,
    InvoiceEvent,
    utcnow,
)


class MockFiscalProvider(FiscalProvider):
    """
    Provider 100% ficticio.
    Nao chama SEFAZ, nao usa certificado, nao emite NF-e real e nao implementa layout fiscal oficial.
    """

    def issue_invoice(self, order):
        invoice = order.invoice
        if invoice is None:
            invoice = Invoice(order=order)
            db.session.add(invoice)
        errors = validate_order(order)

        if errors:
            invoice.status = FISCAL_REJEITADA
            invoice.invoice_number = invoice.invoice_number or f"REJ-{order.id:06d}"
            invoice.invoice_series = "TST"
            invoice.access_key = invoice.access_key or self._fake_access_key(order.id)
            invoice.rejection_reason = "; ".join(errors)
            invoice.issued_at = utcnow()
            order.fiscal_status = FISCAL_REJEITADA
            db.session.add(invoice)
            db.session.flush()
            self._add_event(invoice, "rejected", invoice.rejection_reason, {"errors": errors, "fake": True})
            return invoice

        invoice.status = FISCAL_AUTORIZADA
        now = utcnow()
        invoice.invoice_number = invoice.invoice_number or f"{now.strftime('%H%M')}{order.id:04d}"
        invoice.invoice_series = "TST"
        invoice.access_key = invoice.access_key or self._fake_access_key(order.id)
        invoice.rejection_reason = None
        invoice.issued_at = now
        order.fiscal_status = FISCAL_AUTORIZADA
        db.session.add(invoice)
        db.session.flush()
        self._add_event(
            invoice,
            "authorized",
            "NF-e ficticia autorizada no provedor mock local.",
            {"fake": True, "provider": "MockFiscalProvider"},
        )
        return invoice

    def get_invoice_status(self, invoice):
        return invoice.status

    def download_xml(self, invoice):
        storage_path = self._storage_path("xml")
        filename = f"nfe-fake-{invoice.id}.xml"
        full_path = storage_path / filename
        full_path.write_text(self._xml_content(invoice), encoding="utf-8")
        invoice.xml_path = f"invoices/xml/{filename}"
        self._add_event(invoice, "xml_generated", "XML fake gerado para teste local.", {"path": invoice.xml_path})
        return full_path

    def download_pdf(self, invoice):
        storage_path = self._storage_path("pdf")
        filename = f"nfe-fake-{invoice.id}.pdf"
        full_path = storage_path / filename
        full_path.write_bytes(self._pdf_content(invoice))
        invoice.pdf_path = f"invoices/pdf/{filename}"
        self._add_event(invoice, "pdf_generated", "PDF fake gerado para teste local.", {"path": invoice.pdf_path})
        return full_path

    def _fake_access_key(self, order_id):
        return f"FAKE-{order_id:06d}-{uuid.uuid4().hex[:32].upper()}"

    def _storage_path(self, subfolder):
        path = Path(current_app.config["STORAGE_DIR"]) / "invoices" / subfolder
        path.mkdir(parents=True, exist_ok=True)
        return path

    def _add_event(self, invoice, event_type, message, payload):
        db.session.add(
            InvoiceEvent(
                invoice=invoice,
                event_type=event_type,
                message=message,
                payload_json=payload,
            )
        )

    def _xml_content(self, invoice):
        order = invoice.order
        buyer = order.buyer
        address = buyer.addresses[0] if buyer and buyer.addresses else None
        lines = [
            '<?xml version="1.0" encoding="UTF-8"?>',
            '<simulacao_nfe ambiente="teste" documento="fake">',
            "  <finalidade>Validar fluxo de download, conferencia e arquivo de notas fiscais ficticias em ambiente de teste.</finalidade>",
            "  <declaracao>Este arquivo nao e NF-e real, nao possui validade fiscal, nao foi enviado para SEFAZ e nao deve ser usado em operacao real.</declaracao>",
            "  <corpo>",
            "    <titulo>Nota fiscal ficticia para simulacao operacional</titulo>",
            "    <texto>Documento gerado para demonstrar como uma nota poderia ser organizada no sistema antes de qualquer integracao fiscal real.</texto>",
            "  </corpo>",
            "  <resumo>",
            f"    <pedido>{self._escape(order.marketplace_order_id)}</pedido>",
            f"    <marketplace>{self._escape(order.marketplace)}</marketplace>",
            f"    <numero_ficticio>{self._escape(invoice.invoice_number)}</numero_ficticio>",
            f"    <serie_ficticia>{self._escape(invoice.invoice_series)}</serie_ficticia>",
            f"    <chave_ficticia>{self._escape(invoice.access_key)}</chave_ficticia>",
            f"    <status>{self._escape(invoice.status)}</status>",
            f"    <valor_produtos>{order.total_amount}</valor_produtos>",
            f"    <frete>{order.shipping_amount}</frete>",
            f"    <desconto>{order.discount_amount}</desconto>",
            f"    <taxas_marketplace>{order.marketplace_fee}</taxas_marketplace>",
            f"    <valor_liquido>{order.net_amount}</valor_liquido>",
            "  </resumo>",
            "  <comprador_ficticio>",
            f"    <nome>{self._escape(buyer.name if buyer else 'Comprador ficticio ausente')}</nome>",
            f"    <documento>{self._escape(buyer.document if buyer else '')}</documento>",
            f"    <email>{self._escape(buyer.email if buyer else '')}</email>",
            f"    <telefone>{self._escape(buyer.phone if buyer else '')}</telefone>",
            "  </comprador_ficticio>",
            "  <endereco_ficticio>",
            f"    <logradouro>{self._escape(address.street if address else '')}</logradouro>",
            f"    <numero>{self._escape(address.number if address else '')}</numero>",
            f"    <bairro>{self._escape(address.neighborhood if address else '')}</bairro>",
            f"    <cidade>{self._escape(address.city if address else '')}</cidade>",
            f"    <estado>{self._escape(address.state if address else '')}</estado>",
            f"    <cep>{self._escape(address.zip_code if address else '')}</cep>",
            "  </endereco_ficticio>",
            "  <itens>",
        ]
        for item in order.items:
            lines.extend(
                [
                    "    <item>",
                    f"      <sku>{self._escape(item.sku)}</sku>",
                    f"      <produto>{self._escape(item.product_name)}</produto>",
                    f"      <quantidade>{item.quantity}</quantidade>",
                    f"      <valor_unitario>{item.unit_price}</valor_unitario>",
                    f"      <valor_total>{item.total_price}</valor_total>",
                    f"      <classificacao_fiscal_produto_ncm>{self._escape(item.ncm or 'SEM_CLASSIFICACAO_FISCAL')}</classificacao_fiscal_produto_ncm>",
                    f"      <codigo_fiscal_operacao_cfop>{self._escape(item.cfop or 'SEM_CODIGO_FISCAL_OPERACAO')}</codigo_fiscal_operacao_cfop>",
                    "    </item>",
                ]
            )
        lines.extend(
            [
                "  </itens>",
                "  <auditoria>",
                f"    <gerado_em>{self._escape(utcnow().isoformat(timespec='seconds'))}</gerado_em>",
                "    <provedor>MockFiscalProvider</provedor>",
                "    <integracao_real>false</integracao_real>",
                "  </auditoria>",
                "</simulacao_nfe>",
            ]
        )
        return "\n".join(lines)

    def _pdf_content(self, invoice):
        return build_fake_danfe_pdf(invoice)

    def _escape(self, value):
        if value is None:
            return ""
        text = str(value)
        return (
            text.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
            .replace("'", "&apos;")
        )
