import random

from cached_property import cached_property
from faker import Factory

from populous.exceptions import GenerationError
from populous.exceptions import ValidationError
from populous.vars import Expression, parse_vars
from populous.bloom import BloomFilter

fake = Factory.create()


class BaseGenerator(object):

    def __init__(self, item, field_name, **kwargs):
        self.item = item
        self.field_name = field_name
        self.blueprint = item.blueprint

        # make a copy of the kwargs for inheritance
        self.kwargs = kwargs
        self.get_arguments(**kwargs)

    def __iter__(self):
        return self

    def next(self):
        return next(self.iterator)

    __next__ = next

    @cached_property
    def iterator(self):
        return iter(self.get_generator())

    def get_generator(self):
        return self.generate()

    def generate(self):
        raise NotImplementedError()

    def get_arguments(self, shadow=False, **kwargs):
        # should this field be written in the table?
        self.shadow = shadow

        if kwargs:
            raise ValidationError(
                "Item '{}', field '{}': Got extra param(s) for generator "
                "'{}': {}".format(
                    self.item.name, self.field_name, type(self).__name__,
                    ', '.join(kwargs.keys())
                )
            )

    def evaluate(self, value):
        if isinstance(value, Expression):
            return value.evaluate(**self.blueprint.vars)
        return value

    def parse_vars(self, value):
        return parse_vars(value)


class NullableMixin(object):

    def get_arguments(self, nullable=0, **kwargs):
        super(NullableMixin, self).get_arguments(**kwargs)

        if not nullable:
            self.nullable = 0
        elif nullable is True:
            self.nullable = 0.5
        else:
            self.nullable = self.parse_vars(nullable)

    def get_generator(self):
        if self.nullable:
            return self.generate_with_null()
        return super(NullableMixin, self).get_generator()

    def generate_with_null(self):
        generator = super(NullableMixin, self).get_generator()
        while True:
            if random.random() <= self.evaluate(self.nullable):
                yield None
            else:
                yield next(generator)


class UniquenessMixin(object):
    MAX_TRIES = 10000

    def get_arguments(self, unique=False, **kwargs):
        super(UniquenessMixin, self).get_arguments(**kwargs)

        self.unique = bool(unique)
        if isinstance(unique, (list, tuple)):
            self.unique_with = tuple(unique)
        elif unique and unique is not True:
            self.unique_with = (unique,)
        else:
            self.unique_with = None

        # default bloomfilter, used if for some reason a pre-filled
        # one is not assigned in Item.preprocess
        self.seen = BloomFilter()

    def get_generator(self):
        if self.unique:
            return self.generate_uniquely()
        return super(UniquenessMixin, self).get_generator()

    def generate_uniquely(self):
        seen = self.seen
        unique_with = self.unique_with
        tries = 0
        for value in super(UniquenessMixin, self).get_generator():
            if isinstance(value, tuple) and hasattr(value, 'id'):
                key = value.id
            else:
                key = value
            if unique_with:
                this = self.blueprint.vars['this']
                key = (key,) + tuple(getattr(this, f) for f in unique_with)
            if key in seen:
                tries += 1
                if tries > self.MAX_TRIES:
                    raise GenerationError(
                        "Item '{}', field '{}': Could not generate a "
                        "new unique value in {} tries. Aborting."
                        .format(self.item.name, self.field_name,
                                self.MAX_TRIES)
                    )
                continue
            tries = 0
            seen.add(key, check=False)
            yield value


class Generator(NullableMixin, UniquenessMixin, BaseGenerator):
    pass
