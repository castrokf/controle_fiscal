from pathlib import Path
from shutil import copy2

from flask import Blueprint, abort, current_app, flash, redirect, render_template, send_file, url_for
from flask_login import login_required

from app.audit import record_audit
from app.extensions import db
from app.fiscal.nfe_service import NFeService
from app.models import Invoice

bp = Blueprint("fiscal", __name__, url_prefix="/fiscal")


@bp.get("/")
@login_required
def index():
    invoices = Invoice.query.order_by(Invoice.created_at.desc()).limit(200).all()
    return render_template("fiscal/index.html", invoices=invoices)


@bp.post("/invoices/<int:invoice_id>/generate-files")
@login_required
def generate_files(invoice_id):
    invoice = db.get_or_404(Invoice, invoice_id)
    NFeService().generate_fake_files(invoice)
    flash("Arquivos fiscais simulados gerados.", "success")
    return redirect(url_for("fiscal.index"))


@bp.get("/invoices/<int:invoice_id>/download/<file_type>")
@login_required
def download(invoice_id, file_type):
    if file_type not in {"xml", "pdf"}:
        abort(404)

    invoice = db.get_or_404(Invoice, invoice_id)
    NFeService().generate_fake_files(invoice)
    relative_path = invoice.xml_path if file_type == "xml" else invoice.pdf_path

    storage_root = Path(current_app.config["STORAGE_DIR"]).resolve()
    file_path = (storage_root / relative_path).resolve()
    if storage_root not in file_path.parents:
        abort(403)
    if not file_path.exists():
        abort(404)

    local_copy_path = _copy_to_local_downloads(file_path)
    record_audit(
        f"invoice.download_{file_type}",
        entity_type="invoice",
        entity_id=invoice.id,
        status="OK",
        message=_download_message(file_type, local_copy_path),
    )
    db.session.commit()
    mimetype = "application/xml" if file_type == "xml" else "application/pdf"
    return send_file(file_path, as_attachment=True, download_name=file_path.name, mimetype=mimetype)


def _copy_to_local_downloads(file_path):
    if not current_app.config.get("LOCAL_DOWNLOAD_COPY_ENABLED"):
        return None

    target_dir = Path(current_app.config["LOCAL_DOWNLOAD_DIR"]).expanduser().resolve()
    target_dir.mkdir(parents=True, exist_ok=True)
    target_path = target_dir / file_path.name
    copy2(file_path, target_path)
    return target_path


def _download_message(file_type, local_copy_path):
    base_message = f"Download protegido de {file_type.upper()} simulado."
    if local_copy_path:
        return f"{base_message} Copia local salva em {local_copy_path}."
    return base_message
