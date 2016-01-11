import random

from faker import Factory

from cached_property import cached_property

fake = Factory.create()


class Generator(object):
    def __init__(self, blueprint=None, item_name=None, nullable=False):
        self.blueprint = blueprint
        self.item_name = item_name

        if not nullable:
            self.nullable = 0
        else:
            self.nullable = 0.5 if nullable is True else nullable

    @cached_property
    def item(self):
        return self.blueprint[self.item_name]

    def __call__(self):
        if self.nullable:
            return self.generate_with_null()

        return self.generate()

    def generate_with_null(self):
        for value in self.generate():
            if random.random() <= self.nullable:
                yield None
            else:
                yield value

    def generate(self):
        raise NotImplementedError
