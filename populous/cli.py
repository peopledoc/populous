import click


@click.group()
@click.version_option()
def cli():
    pass


@cli.command()
def hello():
    click.echo("Hello World!")
