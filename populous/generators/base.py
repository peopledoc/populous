from faker import Factory

from cached_property import cached_property

fake = Factory.create()


class Generator(object):
    def __init__(self, blueprint=None, item_name=None, nullable=False):
        self.nullable = nullable
        self.blueprint = blueprint
        self.item_name = item_name

    @cached_property
    def item(self):
        return self.blueprint[self.item_name]

    def __call__(self):
        return self.generate()

    def generate(self):
        raise NotImplementedError
