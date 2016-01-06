import click

from .loader import load_yaml
from .blueprint import Blueprint
from .exceptions import ValidationError, YAMLError, BackendError


def get_blueprint(*files):
    try:
        return Blueprint.from_description(load_yaml(*files))
    except (YAMLError, ValidationError) as e:
        raise click.ClickException(e.message)
    except Exception as e:
        raise click.ClickException("Unexpected error during the blueprint "
                                   "loading: {}".format(e.message))


@click.group()
@click.version_option()
def cli():
    pass


@cli.group()
def run():
    pass


@run.command()
@click.option('--host', default='localhost', help="Database host address")
@click.option('--port', default=5432, type=int, help="Database host port")
@click.option('--db', help="Database name")
@click.option('--user', help="Postgresql user name used to authenticate")
@click.option('--password', help="Postgresql password used to authenticate")
@click.argument('files', nargs=-1, required=True)
def postgresql(host, port, db, user, password, files):
    blueprint = get_blueprint(*files)

    try:
        from populous.backends.postgres import Postgres

        backend = Postgres(database=db, user=user, password=password,
                           host=host, port=port)

        try:
            backend.generate(blueprint)
        finally:
            backend.close()

    except BackendError as e:
        raise click.ClickException(e.message)


@cli.command()
@click.argument('files', nargs=-1, required=True)
def predict(files):
    """
    Predict how many objects will be created if the given files are used.
    """
    blueprint = get_blueprint(*files)

    for item in blueprint:
        click.echo("{name}: {count} {by}".format(
            name=item.name, count=item.total,
            by="({} by {})".format(item.count.number, item.count.by)
               if item.count.by else ""
        ))
