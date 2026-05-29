from datetime import datetime
from decimal import Decimal


def money_br(value):
    if value is None:
        value = 0
    value = Decimal(str(value))
    formatted = f"{value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R$ {formatted}"


def datetime_br(value):
    if not value:
        return "-"
    if isinstance(value, str):
        try:
            value = datetime.fromisoformat(value)
        except ValueError:
            return value
    return value.strftime("%d/%m/%Y %H:%M")


def date_br(value):
    if not value:
        return "-"
    return value.strftime("%d/%m/%Y")


def mask_document(value):
    if not value:
        return "-"
    text = str(value)
    if len(text) <= 6:
        return "***"
    return f"{text[:4]}****{text[-4:]}"


def mask_email(value):
    if not value or "@" not in value:
        return "-"
    name, domain = value.split("@", 1)
    visible = name[:2] if len(name) >= 2 else name[:1]
    return f"{visible}***@{domain}"


def mask_phone(value):
    if not value:
        return "-"
    text = str(value)
    return f"****{text[-4:]}" if len(text) >= 4 else "****"


def status_class(status):
    status = (status or "").upper()
    if "AUTORIZADA" in status or "CONCLUIDO" in status or status in {"OK", "PAGO", "XML_FAKE_GERADO", "PDF_FAKE_GERADO"}:
        return "success"
    if "PENDENTE" in status or "SEM_NFE" in status or "PRONTO" in status:
        return "warning"
    if "REJEITADA" in status or "ERRO" in status or "INCOMPLETOS" in status or "CANCELADO" in status:
        return "danger"
    if "EMITINDO" in status or "PROCESSANDO" in status or "IMPORTADO" in status or "NOVO" in status:
        return "primary"
    return "secondary"


def status_label(status):
    labels = {
        "NOVO": "Novo",
        "IMPORTADO": "Importado",
        "EM_PROCESSAMENTO": "Em processamento",
        "ENVIADO": "Enviado",
        "CANCELADO": "Cancelado",
        "CONCLUIDO": "Concluido",
        "PENDENTE": "Pendente",
        "PAGO": "Pago",
        "SEM_NFE": "Sem NF-e",
        "DADOS_INCOMPLETOS": "Dados incompletos",
        "PRONTO_PARA_EMITIR": "Pronto para emitir",
        "EMITINDO_NFE": "Emitindo NF-e",
        "NFE_FICTICIA_AUTORIZADA": "NF-e simulada autorizada",
        "NFE_FICTICIA_REJEITADA": "NF-e simulada rejeitada",
        "XML_FAKE_GERADO": "XML gerado",
        "PDF_FAKE_GERADO": "PDF gerado",
        "OK": "OK",
        "ERRO": "Erro",
    }
    if not status:
        return "Sem informacao"
    return labels.get(str(status).upper(), str(status).replace("_", " ").title())
