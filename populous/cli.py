import importlib
import logging

import click
import click_log
import six

from .loader import load_blueprint
from .exceptions import ValidationError, YAMLError, BackendError

logger = logging.getLogger('populous')
click_log.basic_config(logger)


def get_blueprint(files, **kwargs):
    try:
        return load_blueprint(*files, **kwargs)
    except (YAMLError, ValidationError) as e:
        raise click.ClickException(six.text_type(e))
    except Exception as e:
        raise click.ClickException("Unexpected error during the blueprint "
                                   "loading: {}".format(e))


@click.group()
@click.version_option()
@click_log.simple_verbosity_option(logger)
def cli():
    pass


@cli.group()
def run():
    pass


def _generic_run(modulename, classname, files, **kwargs):
    try:
        try:
            module = importlib.import_module(
                'populous.backends.' + modulename,
                package='populous.backends'
            )
            backend_cls = getattr(module, classname)
        except (ImportError, AttributeError):
            raise click.ClickException("Backend not found.")

        backend = backend_cls(**kwargs)
        blueprint = get_blueprint(files, backend=backend)

        try:
            with backend.transaction():
                blueprint.generate()

                logger.info("Closing DB transaction...")

        finally:
            backend.close()

        logger.info("Have fun!")

    except BackendError as e:
        raise click.ClickException(six.text_type(e))


@run.command()
@click.option('--host', help="Database host address")
@click.option('--port', type=int, help="Database host port")
@click.option('--db', help="Database name")
@click.option('--user', help="Postgresql user name used to authenticate")
@click.option('--password', help="Postgresql password used to authenticate")
@click.argument('files', nargs=-1, required=True)
def postgres(host, port, db, user, password, files):
    return _generic_run('postgres', 'Postgres', files, host=host, port=port,
                        db=db, user=user, password=password)


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
