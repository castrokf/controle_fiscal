from app.audit import record_audit
from app.extensions import db
from app.fiscal.mock_provider import MockFiscalProvider
from app.fiscal.validators import validate_order
from app.models import FISCAL_DADOS_INCOMPLETOS, FISCAL_EMITINDO, FISCAL_PRONTO


class NFeService:
    def __init__(self, provider=None):
        self.provider = provider or MockFiscalProvider()

    def validate_order(self, order):
        errors = validate_order(order)
        if errors:
            order.fiscal_status = FISCAL_DADOS_INCOMPLETOS
            record_audit(
                "fiscal.validation",
                entity_type="marketplace_order",
                entity_id=order.id,
                status="ERRO",
                message="; ".join(errors),
            )
        else:
            order.fiscal_status = FISCAL_PRONTO
            record_audit(
                "fiscal.validation",
                entity_type="marketplace_order",
                entity_id=order.id,
                status="OK",
                message="Operacao pronta para emissao simulada.",
            )
        db.session.commit()
        return errors

    def issue_fake_invoice(self, order):
        order.fiscal_status = FISCAL_EMITINDO
        db.session.flush()
        invoice = self.provider.issue_invoice(order)
        status = "OK" if "AUTORIZADA" in invoice.status else "ERRO"
        record_audit(
            "invoice.issue_fake",
            entity_type="invoice",
            entity_id=invoice.id,
            status=status,
            message=f"Emissao simulada concluida com status {invoice.status}.",
        )
        db.session.commit()
        return invoice

    def generate_fake_files(self, invoice):
        xml_path = self.provider.download_xml(invoice)
        pdf_path = self.provider.download_pdf(invoice)
        record_audit(
            "invoice.files_generated",
            entity_type="invoice",
            entity_id=invoice.id,
            status="OK",
            message="XML e PDF simulados gerados para a nota.",
        )
        db.session.commit()
        return xml_path, pdf_path
