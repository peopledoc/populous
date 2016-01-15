import random

from faker import Factory

fake = Factory.create()


class Generator(object):
    def __init__(self, item, nullable=False):
        self.item = item
        self.blueprint = item.blueprint

        if not nullable:
            self.nullable = 0
        else:
            self.nullable = 0.5 if nullable is True else nullable

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
