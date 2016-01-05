import click

from .loader import load_yaml
from .blueprint import Blueprint
from .exceptions import ValidationError, YAMLError


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
