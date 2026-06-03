import click
from flask import current_app
from flask.cli import with_appcontext
from flask_migrate import upgrade

from app.extensions import db
from app.fake_data import seed_database
from app.models import ROLE_ADMIN, User
from app.security import initial_admin_password_policy_errors, is_valid_email_format, normalize_email


@click.command("deploy")
@with_appcontext
def deploy_command():
    click.echo("Aplicando migrations do banco de dados...")
    upgrade()
    click.echo("Migrations aplicadas com sucesso.")

    config_error = _initial_admin_config_error()
    has_users = User.query.first() is not None

    if has_users:
        if config_error:
            click.echo("Administrador inicial nao sincronizado: " + config_error, err=True)
        else:
            created, email = _sync_initial_admin()
            action = "criado" if created else "atualizado"
            click.echo(f"Administrador inicial {action}: {email}")

        click.echo("Seed automatico ignorado: o banco ja possui usuario cadastrado.")
        return

    if not current_app.config.get("ENABLE_AUTO_SEED"):
        if config_error:
            click.echo("Administrador inicial nao criado: " + config_error, err=True)
        else:
            created, email = _sync_initial_admin()
            action = "criado" if created else "atualizado"
            click.echo(f"Administrador inicial {action}: {email}")

        click.echo("Seed automatico desativado.")
        return

    if config_error:
        click.echo("Seed inicial nao executado: " + config_error, err=True)
        click.echo(
            "O servico continuara subindo. Corrija INITIAL_ADMIN_EMAIL e INITIAL_ADMIN_PASSWORD "
            "no Render e rode Manual Deploy novamente.",
            err=True,
        )
        return

    result = seed_database(reset=True)
    click.echo("Seed inicial executado com sucesso.")
    click.echo(f"Usuarios: {result['users']}")
    click.echo(f"Produtos: {result['products']}")
    click.echo(f"Pedidos: {result['orders']}")
    click.echo(f"Notas fiscais simuladas: {result['invoices']}")
    click.echo(f"Fechamentos diarios: {result['daily_closings']}")


def _initial_admin_config_error():
    email = normalize_email(current_app.config.get("INITIAL_ADMIN_EMAIL"))
    password = current_app.config.get("INITIAL_ADMIN_PASSWORD") or ""

    if not email or not password:
        return "defina INITIAL_ADMIN_EMAIL e INITIAL_ADMIN_PASSWORD."
    if not is_valid_email_format(email):
        return "INITIAL_ADMIN_EMAIL precisa ser um email valido."

    errors = initial_admin_password_policy_errors(password)
    if errors:
        return "INITIAL_ADMIN_PASSWORD nao atende a politica de senha: " + "; ".join(errors) + "."

    return None


def _sync_initial_admin():
    name = (current_app.config.get("INITIAL_ADMIN_NAME") or "Administrador").strip() or "Administrador"
    email = normalize_email(current_app.config.get("INITIAL_ADMIN_EMAIL"))
    password = current_app.config.get("INITIAL_ADMIN_PASSWORD") or ""

    user = User.query.filter_by(email=email).first()
    created = user is None
    if created:
        user = User(email=email, role=ROLE_ADMIN, is_active=True, name=name)
        db.session.add(user)
    else:
        user.name = name
        user.role = ROLE_ADMIN
        user.is_active = True

    user.set_password(password)
    db.session.commit()
    return created, email


@click.command("reset-admin")
@with_appcontext
def reset_admin_command():
    config_error = _initial_admin_config_error()
    if config_error:
        raise click.ClickException(config_error)

    created, email = _sync_initial_admin()
    action = "criado" if created else "atualizado"
    click.echo(f"Administrador {action}: {email}")


@click.command("seed")
@click.option("--reset/--no-reset", default=True, help="Limpa e recria dados simulados antes de popular.")
@with_appcontext
def seed_command(reset):
    result = seed_database(reset=reset)
    click.echo("Seed demo executado com sucesso.")
    click.echo(f"Usuarios: {result['users']}")
    click.echo(f"Produtos: {result['products']}")
    click.echo(f"Pedidos: {result['orders']}")
    click.echo(f"Notas fiscais simuladas: {result['invoices']}")
    click.echo(f"Fechamentos diarios: {result['daily_closings']}")
