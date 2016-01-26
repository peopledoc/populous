import importlib

import click

from .loader import load_yaml
from .blueprint import Blueprint
from .exceptions import ValidationError, YAMLError, BackendError


def get_blueprint(files, **kwargs):
    try:
        return Blueprint.from_description(load_yaml(*files), **kwargs)
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


def _generic_run(modulename, classname, files, **kwargs):
    try:
        try:
            module = importlib.import_module('.' + modulename,
                                             package='populous.backends')
            backend_cls = getattr(module, classname)
        except (ImportError, AttributeError):
            raise click.ClickException("Backend not found.")

        backend = backend_cls(**kwargs)
        blueprint = get_blueprint(files, backend=backend)

        try:
            with backend.transaction() as trans:
                for item in blueprint:
                    if not item.total:
                        continue

                    label = 'Creating {} {}'.format(item.total, item.name)
                    with click.progressbar(label=label,
                                           length=item.total) as bar:
                        for progress in backend.generate(item, trans):
                            bar.update(progress)
        finally:
            backend.close()

    except BackendError as e:
        raise click.ClickException(e.message)


@run.command()
@click.option('--host', default='localhost', help="Database host address")
@click.option('--port', default=5432, type=int, help="Database host port")
@click.option('--db', help="Database name")
@click.option('--user', help="Postgresql user name used to authenticate")
@click.option('--password', help="Postgresql password used to authenticate")
@click.argument('files', nargs=-1, required=True)
def postgresql(host, port, db, user, password, files):
    return _generic_run('postgres', 'Postgres', files, host=host, port=port,
                        database=db, user=user, password=password)


@cli.command()
@click.argument('files', nargs=-1, required=True)
def predict(files):
    """
    Predict how many objects will be created if the given files are used.
    """
    blueprint = get_blueprint(files)

    for item in blueprint:
        click.echo("{name}: {count} {by}".format(
            name=item.name, count=item.total,
            by="({} by {})".format(item.count.number, item.count.by)
               if item.count.by else ""
        ))


@cli.command()
def generators():
    """
    List all the available generators.
    """
    from populous import generators

    base = generators.Generator

    for name in dir(generators):
        generator = getattr(generators, name)

        if isinstance(generator, type) and issubclass(generator, base):
            name = generator.__name__
            doc = (generator.__doc__ or '').strip()

            if doc:
                click.echo("{} - {}".format(name, doc))
            else:
                click.echo(name)
