import click
from flask import current_app
from flask.cli import with_appcontext
from flask_migrate import upgrade

from app.fake_data import seed_database
from app.models import User


@click.command("deploy")
@with_appcontext
def deploy_command():
    click.echo("Aplicando migrations do banco de dados...")
    upgrade()
    click.echo("Migrations aplicadas com sucesso.")

    if not current_app.config.get("ENABLE_AUTO_SEED"):
        click.echo("Seed automatico desativado.")
        return

    if User.query.first():
        click.echo("Seed automatico ignorado: o banco ja possui usuario cadastrado.")
        return

    result = seed_database(reset=True)
    click.echo("Seed inicial executado com sucesso.")
    click.echo(f"Usuarios: {result['users']}")
    click.echo(f"Produtos: {result['products']}")
    click.echo(f"Pedidos: {result['orders']}")
    click.echo(f"Notas fiscais simuladas: {result['invoices']}")
    click.echo(f"Fechamentos diarios: {result['daily_closings']}")


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
