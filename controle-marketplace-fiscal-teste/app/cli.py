import click
from flask.cli import with_appcontext

from app.fake_data import seed_database


@click.command("seed")
@click.option("--reset/--no-reset", default=True, help="Limpa e recria dados ficticios antes de popular.")
@with_appcontext
def seed_command(reset):
    result = seed_database(reset=reset)
    click.echo("Seed ficticio executado com sucesso.")
    click.echo(f"Usuarios: {result['users']}")
    click.echo(f"Produtos: {result['products']}")
    click.echo(f"Pedidos: {result['orders']}")
    click.echo(f"Notas fiscais ficticias: {result['invoices']}")
    click.echo(f"Fechamentos diarios: {result['daily_closings']}")
