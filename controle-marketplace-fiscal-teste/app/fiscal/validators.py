def validate_order(order):
    errors = []

    if not order.buyer:
        errors.append("Comprador ficticio ausente.")
    elif not order.buyer.addresses:
        errors.append("Endereco ficticio do comprador ausente.")

    if not order.items:
        errors.append("Pedido sem itens.")

    for item in order.items:
        if not item.ncm:
            errors.append(f"Item {item.sku} sem classificacao fiscal do produto (NCM).")
        if not item.cfop:
            errors.append(f"Item {item.sku} sem codigo fiscal da operacao (CFOP).")

    return errors


def item_fiscal_status(item):
    missing = []
    if not item.ncm:
        missing.append("classificacao fiscal do produto (NCM)")
    if not item.cfop:
        missing.append("codigo fiscal da operacao (CFOP)")
    if missing:
        return f"Pendente: {', '.join(missing)}"
    return "Completo"
