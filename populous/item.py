import copy
import logging
import random
from collections import OrderedDict
from collections import namedtuple

from cached_property import cached_property

from populous import generators
from populous.compat import zip
from populous.compat import range
from populous.exceptions import ValidationError
from populous.factory import ItemFactory
from populous.vars import parse_vars
from populous.vars import Expression
from populous.vars import ValueExpression

logger = logging.getLogger('populous')

ITEM_KEYS = ('name', 'parent', 'table', 'count', 'fields', 'store_in')
COUNT_KEYS = ('number', 'by', 'min', 'max')


class Item(object):

    def __init__(self, blueprint, name, table, parent=None, store_in=None):
        self.blueprint = blueprint

        if parent:
            table = table or parent.table
            store_in = store_in or parent._store_in

        if not name:
            # if any of our parent had a name we would have inherited it
            raise ValidationError("Items without a parent must have a name.")

        if not table:
            raise ValidationError(
                "Item '{}' does not have a table.".format(name)
            )

        self.name = name
        self.table = table
        self.count = Count(
            number=0, by=None, min=None, max=None, blueprint=blueprint
        )
        self.fields = OrderedDict()
        self._store_in = store_in
        self._set_store_in(store_in)

        self.add_field('id', 'Value', value=None, shadow=True)

        if parent:
            for name, field in parent.fields.items():
                self.add_field(name, type(field).__name__, **field.kwargs)
            self.count = parent.count

        if parent:
            self.ancestors = parent.ancestors
            # only add parent to ancestors if it will not be generated
            # otherwise we would generate our children for both our parent
            # and us
            if parent.count.number == 0:
                self.ancestors += [parent.name]
        else:
            self.ancestors = []

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

    def _set_store_in(self, store_in):
        if not store_in:
            self.store_in_global = {}
            self.store_in_item = {}
            return

        self.store_in_global = {
            name: parse_vars(expression)
            for name, expression in store_in.items()
            if not name.startswith('this.')
        }
        # create the global var in the blueprint
        for name in self.store_in_global:
            self.blueprint.vars.setdefault(name, [])

        self.store_in_item = {
            ValueExpression(name): parse_vars(expression)
            for name, expression in store_in.items()
            if name.startswith('this.')
        }
        # create a "store" generator on the targeted item
        for expr in self.store_in_item:
            target_name, store_name = expr.attrs.rsplit('.')[-2:]
            try:
                target = self.blueprint.items[target_name]
            except KeyError:
                raise ValidationError(
                    "Error in 'store_in' section in item '{}': "
                    "The item '{}' does not exist."
                    .format(self.name, target_name)
                )
            target.add_field(store_name, 'Store')

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
        number = parse_vars(number)
        min = parse_vars(min)
        max = parse_vars(max)

        for key, value in zip(('number', 'min', 'max'), (number, min, max)):
            if value is None:
                continue
            if isinstance(value, int):
                if value < 0:
                    raise ValidationError(
                        "Item '{}' count: {} must be positive."
                        .format(self.name, key)
                    )
            elif not isinstance(value, Expression):
                raise ValidationError(
                    "Item '{}' count: {} must be an integer or a variable "
                    "(got: '{}')."
                    .format(self.name, key, type(value).__name__)
                )

        current_count = self.count
        if current_count:
            # this item already has a count, merge it
            by = by or current_count.by
            if min is None and max is None:
                number = number or current_count.number
            if number is None:
                if min is None:
                    min = current_count.min
                if max is None:
                    max = current_count.max

        if min is not None or max is not None:
            if number is not None:
                raise ValidationError(
                    "Item '{}' count: Cannot set 'number' and 'min/max'."
                    .format(self.name)
                )

        # treat None as 0
        min = min or 0
        max = max or 0

        if isinstance(min, int) and isinstance(max, int) and min > max:
            raise ValidationError(
                "Item '{}' count: Min is greater than max."
                .format(self.name)
            )

        self.count = Count(
            number=number, by=by, min=min, max=max, blueprint=self.blueprint
        )

    def preprocess(self):
        seen_fields = self.blueprint.seen[self.table]
        db_fields = []
        to_fill = []
        for field in self.fields.values():
            if field.shadow or not getattr(field, 'unique'):
                continue

            index = len(db_fields)
            if field.unique_with:
                fields = (field.field_name,) + tuple(field.unique_with)
                if fields not in seen_fields:
                    db_fields += fields
                    to_fill.append((field, slice(index, index + len(fields))))
                field.seen = seen_fields[fields]
            else:
                field_name = field.field_name
                if field_name not in seen_fields:
                    db_fields.append(field_name)
                    to_fill.append((field, index))
                field.seen = seen_fields[field_name]

        if not db_fields:
            return

        for values in self.blueprint.backend.select(self.table, db_fields):
            for field, index in to_fill:
                field.seen.add(values[index], check=False)

    def batch_written(self, buffer, batch, ids):
        logger.info("{:>5} {} written".format(len(batch), self.name))

        objs = tuple(e._replace(id=id) for (e, id) in zip(batch, ids))
        self.store_final_values(objs)
        self.generate_dependencies(buffer, objs)

    def store_final_values(self, objs):
        # replace the temporary stored objects by the final value
        # (now that we know computed fields like 'id')

        def _get_values(expression):
            for obj in objs:
                self.blueprint.vars['this'] = obj
                yield expression.evaluate(**self.blueprint.vars)
            del self.blueprint.vars['this']

        for name, expression in self.store_in_global.items():
            store = self.blueprint.vars[name]
            store[-len(objs):] = _get_values(expression)

        for name_expr, value_expr in self.store_in_item.items():
            stores = {}

            # group the values by each instance of the store,
            # so that we know how many items we have to update
            # for each instance
            for i, obj in enumerate(objs):
                self.blueprint.vars['this'] = obj
                store = name_expr.evaluate(**self.blueprint.vars)
                value = value_expr.evaluate(**self.blueprint.vars)

                holder = stores.setdefault(id(store), (store, []))
                holder[1].append(value)

            del self.blueprint.vars['this']

            # now that we have separated the different instance,
            # we can update the last values
            for store, values in stores.values():
                store[-len(values):] = values

    def store_value(self, obj):
        self.blueprint.vars['this'] = obj

        for name, expression in self.store_in_global.items():
            store = self.blueprint.vars[name]
            value = expression.evaluate(**self.blueprint.vars)
            store.append(value)

        for name_expr, value_expr in self.store_in_item.items():
            store = name_expr.evaluate(**self.blueprint.vars)
            store.append(value_expr.evaluate(**self.blueprint.vars))

        del self.blueprint.vars['this']

    def generate(self, buffer, count, parent=None):
        factory = ItemFactory(self, parent=parent)

        for i in range(count):
            self.blueprint.vars['this'] = factory
            obj = factory.generate()
            del self.blueprint.vars['this']

            self.store_value(obj)
            buffer.add(obj)

    def generate_dependencies(self, buffer, batch):
        # generate items having a "count by" on this item
        # or one of its ancestors
        names = frozenset(self.ancestors) | {self.name}
        for item in self.blueprint.items.values():
            by = item.count.by
            if by in names:
                for obj in batch:
                    self.blueprint.vars[by] = obj
                    count = item.count()
                    del self.blueprint.vars[by]
                    if count:
                        item.generate(buffer, count, parent=obj)
                buffer.write(item)

    def db_values(self, obj):
        return tuple(getattr(obj, field) for field in self.db_fields)


class Count(namedtuple('Count', COUNT_KEYS + ('blueprint',))):
    __slots__ = ()

    def evaluate(self, value):
        if isinstance(value, Expression):
            return value.evaluate(**self.blueprint.vars)
        return value

    def __call__(self):
        if self.number is not None:
            return self.evaluate(self.number)
        return random.randint(self.evaluate(self.min), self.evaluate(self.max))
