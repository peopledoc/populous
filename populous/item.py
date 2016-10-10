import copy
import random
from collections import namedtuple
from itertools import izip

from cached_property import cached_property

from populous import generators
from populous.exceptions import ValidationError
from populous.factory import ItemFactory
from populous.vars import parse_vars

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
        self.count = Count(number=0, by=None, min=None, max=None)
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

        self.add_field('id', 'Value', value=None, shadow=True)

        if parent:
            for name, field in parent.fields.items():
                self.add_field(name, type(field).__name__, **field.kwargs)
            self.count = parent.count

    @cached_property
    def namedtuple(self):
        fields = tuple(self.fields.keys())
        if self.count.by:
            fields += (self.count.by,)
        return namedtuple(self.name, fields)

    @cached_property
    def db_fields(self):
        return tuple(
            name for name, field in self.fields.items() if not field.shadow
        )

    def add_field(self, name, generator, **params):
        if not generator:
            parent_field = self.fields.get(name, None)
            if parent_field:
                # if the field already exists and a new generator
                # has not been set, we use the same generator and the
                # same default params than the existing one
                generator = type(parent_field).__name__
                parent_kwargs = copy.deepcopy(parent_field.kwargs)
                parent_kwargs.update(params)
                params = parent_kwargs
            else:
                raise ValidationError(
                    "Field '{}' in item '{}' must either be a value, or "
                    "a dict with a 'generator' key."
                    .format(name, self.name)
                )

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
                    .format(self.name, key, type(value).__name__)
                )
            if value < 0:
                raise ValidationError(
                    "Item '{}' count: {} must be positive."
                    .format(self.name, key)
                )

        current_count = self.count
        if current_count:
            # this item already has a count, merge it
            by = by or current_count.by
            if min is None and max is None:
                number = number or current_count.number
            if number is None:
                min = min or current_count.min
                max = max or current_count.max

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

    def preprocess(self):
        db_fields = []
        to_fill = []
        for field in self.fields.values():
            if not getattr(field, 'unique'):
                continue

            index = len(db_fields)
            if field.unique_with:
                fields = (field.field_name,) + field.unique_with
                db_fields += fields
                to_fill.append((field, slice(index, index + len(fields))))
            else:
                db_fields.append(field.field_name)
                to_fill.append((field, index))

        if not db_fields:
            return

        for values in self.blueprint.backend.select(self.table, db_fields):
            for field, index in to_fill:
                field.seen.add(values[index], check=False)

    def batch_written(self, buffer, batch, ids):
        objs = tuple(e._replace(id=id) for (e, id) in izip(batch, ids))
        self.store_values(objs)
        self.generate_dependencies(buffer, objs)

    def store_values(self, objs):
        def _get_values(expression):
            for obj in objs:
                self.blueprint.vars['this'] = obj
                yield expression.evaluate(**self.blueprint.vars)
            del self.blueprint.vars['this']

        for name, expression in self.store_in.items():
            store = self.blueprint.vars[name]
            store.extend(_get_values(expression))

    def generate(self, buffer, count, parent=None):
        factory = ItemFactory(self, parent=parent)

        for i in xrange(count):
            self.blueprint.vars['this'] = factory
            obj = factory.generate()
            del self.blueprint.vars['this']

            buffer.add(obj)

    def generate_dependencies(self, buffer, batch):
        for item in self.blueprint.items.values():
            if item.count.by != self.name:
                # we only want our direct children
                continue

            for obj in batch:
                item.generate(buffer, item.count(), parent=obj)

    def db_values(self, obj):
        return tuple(getattr(obj, field) for field in self.db_fields)


class Count(namedtuple('Count', COUNT_KEYS)):
    __slots__ = ()

    def __call__(self):
        if self.number is not None:
            return self.number
        return random.randint(self.min, self.max)
