from __future__ import absolute_import

import argparse
from collections import OrderedDict
from functools import partial

from django.apps import apps
from django.core import validators
from django.core.management.base import BaseCommand
from django.db import models

import yaml
from cached_property import cached_property


class SkipField(Exception):
    pass


class Command(BaseCommand):
    help = """
    This command will print a blueprint for Populous corresponding to all
    the models in the given apps.

    Example:
        $ django-admin populous auth myapp > blueprints/00-schema.yml

    The goal is not to generate a read-to-use blueprint, but to bootstrap
    it by doing all the heavy-lifting.
    In most cases the created blueprint will not be advanced
    enough to generate data respecting all your business or even technical
    constraints.

    Django fields are mapped to the most suitable generator, but
    sometimes, this might not be possible.
    In this case the field will be reprensented as a null value, and you'll
    have to override it. Please refer to Populous documentation to see how
    to do that.

    The fields not handled by this command are relational fields (ForeignKey,
    OneToOneField, ManyToManyField) and some specialized fields like
    CommaSeparatedIntegerField or FileField.

    This command identify unique fields, but not fields that are unique
    together. This is by design, because the command cannot know which
    is the field that should change when a duplicate is found during
    the generation.
    """

    def add_arguments(self, parser):
        # don't mess with the help text
        parser.formatter_class = argparse.RawDescriptionHelpFormatter
        parser.add_argument('apps', nargs='+')

    def handle(self, *args, **options):
        blueprint = {
            'items': list(self.export_models(options['apps']))
        }
        self.stdout.write(self.dump(blueprint))

    def dump(self, blueprint):
        class Dumper(yaml.SafeDumper):
            pass

        def _ordered_representer(dumper, data):
            return dumper.represent_mapping(
                yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
                data.items(),
                flow_style=False  # avoid dumping using inline representation
            )

        Dumper.add_representer(OrderedDict, _ordered_representer)
        return yaml.dump(blueprint, Dumper=Dumper, indent=2)

    def export_models(self, app_labels):
        # TODO: handle through table
        for app_label in app_labels:
            app = apps.get_app_config(app_label)
            for model in app.get_models():
                if model._meta.abstract:
                    continue
                yield self.export_model(model)

    def export_model(self, model):
        return OrderedDict((
            ('name', model.__name__),
            ('table', model._meta.db_table),
            ('fields', OrderedDict(self.export_fields(model))),
        ))

    def export_fields(self, model):
        for field in model._meta.get_fields():
            if not field.concrete or field.primary_key:
                continue
            try:
                yield self.export_field(field)
            except SkipField:
                continue

    def export_field(self, field):
        params = None

        if field.choices:
            params = OrderedDict((
                ('generator', 'Choices'),
                ('choices', [choice[0] for choice in field.choices])
            ))
        else:
            try:
                handler = next(
                    handler for field_type, handler in self.fields_mapping
                    if isinstance(field, field_type)
                )
            except StopIteration:
                raise SkipField()

            if handler:
                params = handler(field)
            else:
                params = None

        if params is not None:
            if 'nullable' not in params and field.null:
                params['nullable'] = True

            if 'unique' not in params and field.unique:
                params['unique'] = True

        # TODO: handle unique_for_date/month/year when filters are implemented

        return field.db_column or field.name, params

    @cached_property
    def fields_mapping(self):
        params = [
            (models.AutoField, self.skip),
            (models.BigIntegerField, self.handle_integer),
            (models.BinaryField, None),
            (models.BooleanField, self.handle_boolean),
            (models.CommaSeparatedIntegerField, None),
            (models.DateField, partial(self.handle_datetime, date=True)),
            (models.DateTimeField, self.handle_datetime),
            (models.DecimalField, None),
            (models.DurationField, None),
            (models.EmailField, partial(self.handle_text, generator='Email')),
            (models.FileField, None),
            (models.FilePathField, None),
            (models.FloatField, None),
            (models.ImageField, None),
            (models.IntegerField, self.handle_integer),
            (models.GenericIPAddressField, self.handle_ip),
            (models.NullBooleanField, self.handle_boolean),
            (models.PositiveIntegerField, self.handle_integer),
            (models.PositiveSmallIntegerField, self.handle_integer),
            (models.SlugField, None),
            (models.SmallIntegerField, self.handle_integer),
            (models.TextField, self.handle_text),
            (models.TimeField, None),
            (models.URLField, partial(self.handle_text, generator='URL')),
            (models.UUIDField, self.handle_uuid),
            (models.CharField, self.handle_text),
            (models.ForeignKey, None),
            (models.OneToOneField, None),
            (models.ManyToManyField, self.skip)
        ]

        try:
            # Django < 1.9
            params.append((models.IPAddressField, self.handle_ip))
        except AttributeError:
            pass

        try:
            # Django >= 1.10
            params.append((models.BigAutoField, self.skip))
        except AttributeError:
            pass

        return params

    def skip(self, field):
        raise SkipField()

    def handle_integer(self, field):
        params = OrderedDict((
            ('generator', 'Integer'),
        ))
        for validator in field.validators:
            if isinstance(validator, validators.MinValueValidator):
                params['min'] = validator.limit_value
            elif isinstance(validator, validators.MaxValueValidator):
                params['max'] = validator.limit_value
        return params

    def handle_boolean(self, field):
        return OrderedDict((
            ('generator', 'Boolean'),
        ))

    def handle_text(self, field, generator='Text'):
        params = OrderedDict((
            ('generator', generator),
            ('min_length', 0 if field.blank else 1),
        ))
        if field.max_length is not None:
            params['max_length'] = field.max_length
        return params

    def handle_datetime(self, field, date=False):
        params = OrderedDict((
            ('generator', 'Date' if date else 'DateTime'),
        ))
        if field.auto_now or field.auto_now_add:
            # make sure we don't set a created_at or updated_at field
            # to a future value
            # (this might be useless as it is the default of populous)
            params['past'] = True
            params['future'] = False
        return params

    def handle_ip(self, field):
        protocol = getattr(field, 'protocol', 'IPv4')
        return OrderedDict((
            ('generator', 'IP'),
            ('ipv4', protocol in ('both', 'IPv4')),
            ('ipv6', protocol in ('both', 'IPv6')),
        ))

    def handle_uuid(self, field):
        return OrderedDict((
            ('generator', 'UUID'),
            # This is a hack to avoid checking the value for uniqueness for
            # uuid fields, as it would be worthless
            ('unique', False),
        ))
