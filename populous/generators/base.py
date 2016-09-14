import random

from cached_property import cached_property
from faker import Factory

from populous.exceptions import ValidationError
from populous.generators.vars import Expression

fake = Factory.create()


class BaseGenerator(object):

    def __init__(self, item, field_name, **kwargs):
        self.item = item
        self.field_name = field_name
        self.blueprint = item.blueprint

        self.get_arguments(**kwargs)

    def __iter__(self):
        return self

    def next(self):
        return next(self.iterator)

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


class NullableMixin(object):

    def get_arguments(self, nullable=0, **kwargs):
        super(NullableMixin, self).get_arguments(**kwargs)

        if not nullable:
            self.nullable = 0
        else:
            self.nullable = 0.5 if nullable is True else nullable

    def get_generator(self):
        if self.nullable:
            return self.generate_with_null()
        return super(NullableMixin, self).get_generator()

    def generate_with_null(self):
        for value in super(NullableMixin, self).get_generator():
            if random.random() <= self.nullable:
                yield None
            else:
                yield value


class Generator(NullableMixin, BaseGenerator):
    pass
