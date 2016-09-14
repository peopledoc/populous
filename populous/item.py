import random
from collections import namedtuple

from cached_property import cached_property

from populous import generators
from populous.exceptions import ValidationError
from populous.factory import ItemFactory
from populous.generators.vars import parse_vars

ITEM_KEYS = ('name', 'parent', 'table', 'count', 'fields', 'store_in')
COUNT_KEYS = ('number', 'by', 'min', 'max')


class Item(object):

    def __init__(self, blueprint, name, table, parent=None, store_in=None):
        self.blueprint = blueprint

        if parent:
            table = table or parent.table
            store_in = store_in or parent.store_in

        if not name:
            # if any of our parent had a name we would have inherited it
            raise ValidationError("Items without a parent must have a name.")

        if not table:
            raise ValidationError(
                "Item '{}' does not have a table.".format(name)
            )

        self.name = name
        self.table = table
        self.count = None
        self.fields = {}

        if store_in:
            self.store_in = {
                name: parse_vars(expression)
                for name, expression in store_in.items()
            }
            for name in self.store_in:
                self.blueprint.vars.setdefault(name, [])
        else:
            self.store_in = {}

        self.add_field('id', 'IntegerPrimaryKey')

        if parent:
            for name, field in parent.fields.items():
                # TODO: copy
                self.fields[name] = field
            self.add_count(parent.count.number, parent.count.by,
                           parent.count.min, parent.count.max)

    @cached_property
    def namedtuple(self):
        return namedtuple(self.name, self.db_fields)

    @cached_property
    def db_fields(self):
        return tuple(
            name for name, field in self.fields.items() if not field.shadow
        )

    def add_field(self, name, generator, **params):
        try:
            generator_cls = getattr(generators, generator)
        except AttributeError:
            raise ValidationError(
                "Item '{}', field '{}': Generator '{}' does not exist."
                .format(self.name, name, generator)
            )
        self.fields[name] = generator_cls(self, name, **params)

    def add_count(self, number=None, by=None, min=None, max=None):
        for key, value in zip(('number', 'min', 'max'), (number, min, max)):
            if value is None:
                continue
            if not isinstance(value, int):
                raise ValidationError(
                    "Item '{}' count: {} must be an integer (got: '{}')."
                    .format(self.name, key, type(value))
                )
            if value < 0:
                raise ValidationError(
                    "Item '{}' count: {} must be positive."
                    .format(self.name, key)
                )

        if min is not None or max is not None:
            if number is not None:
                raise ValidationError(
                    "Item '{}' count: Cannot set 'number' and 'min/max'."
                    .format(self.name)
                )

        # treat None as 0
        min = min or 0
        max = max or 0

        if min > max:
            raise ValidationError(
                "Item '{}' count: Min is greater than max."
                .format(self.name)
            )

        self.count = Count(number=number, by=by, min=min, max=max)

    def store_values(self, factory):
        for name, expression in self.store_in.items():
            store = self.blueprint.vars[name]
            store.append(expression.evaluate(**self.blueprint.vars))

    def generate(self, buffer):
        dependencies = tuple(item for item in self.blueprint.items.values()
                             if item.count.by == self.name)

        for i in xrange(self.count()):
            factory = ItemFactory(self)

            self.blueprint.vars['this'] = factory
            buffer.add(factory.generate())
            self.store_values(factory)
            del self.blueprint.vars['this']

            self.blueprint.vars[self.name] = factory
            for dependency in dependencies:
                dependency.generate(buffer)
            del self.blueprint.vars[self.name]


class Count(namedtuple('Count', COUNT_KEYS)):
    __slots__ = ()

    def __call__(self):
        if self.number is not None:
            return self.number
        return random.randint(self.min, self.max)
