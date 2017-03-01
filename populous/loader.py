import yaml
from collections import OrderedDict

from .blueprint import Blueprint
from .exceptions import ValidationError
from .exceptions import YAMLError


BLUEPRINT_KEYS = ('fixtures', 'items', 'vars')


def load_blueprint(*filenames, **kwargs):
    blueprint = Blueprint(**kwargs)

    for filename in filenames:
        content = _get_yaml(filename)
        try:
            _load_content(blueprint, content)
        except ValidationError as e:
            e.filename = filename
            raise e

    return blueprint


def _get_yaml(filename):
    class OrderedLoader(yaml.Loader):
        pass

    def construct_mapping(loader, node):
        loader.flatten_mapping(node)
        return OrderedDict(loader.construct_pairs(node))

    OrderedLoader.add_constructor(
        yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
        construct_mapping
    )

    with open(filename) as f:
        try:
            return yaml.load(f, OrderedLoader)
        except yaml.YAMLError as e:
            raise YAMLError(filename, str(e))


def _load_content(blueprint, content):
    if not content:
        return

    if not isinstance(content, dict):
        raise ValidationError(
            "The blueprint must be a dict containing the keys 'vars' and "
            "'items'. Got a '{}'.".format(type(content).__name__)
        )

    if any(key not in BLUEPRINT_KEYS for key in content.keys()):
        extra = set(content.keys()) - set(BLUEPRINT_KEYS)
        raise ValidationError(
            "Unknown key(s) in blueprint: '{}'. Possible keys are: '{}'."
            .format(', '.join(sorted(extra)), ', '.join(BLUEPRINT_KEYS))
        )

    _load_vars(blueprint, content.get('vars', {}))
    _load_items(blueprint, content.get('items', []))
    _load_fixtures(blueprint, content.get('fixtures', {}))


def _load_vars(blueprint, vars_):
    if not isinstance(vars_, dict):
        raise ValidationError(
            "Blueprint vars must be a dict, not a {}."
            .format(type(vars_).__name__)
        )

    for name, value in vars_.items():
        blueprint.add_var(name, value)


def _load_items(blueprint, items):
    if not isinstance(items, list):
        raise ValidationError(
            "Blueprint items must be in a list, not a {}."
            .format(type(items).__name__)
        )

    for item in items:
        blueprint.add_item(item)


def _load_fixtures(blueprint, fixtures):
    if not isinstance(fixtures, dict):
        raise ValidationError(
            "Blueprint fixtures must be in a dict, not a {}."
            .format(type(fixtures).__name__)
        )

    for item, values in fixtures.items():
        if not isinstance(values, dict):
            raise ValidationError(
                "Fixtures for item '{}' must be in a dict, not a {}."
                .format(item, type(values).__name__)
            )

        for name, fixture in values.items():
            blueprint.add_fixture(item, name, fixture)
