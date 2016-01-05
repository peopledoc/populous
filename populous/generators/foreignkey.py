import random

from .base import Generator


class ForeignKey(Generator):

    def __init__(self, target=None, field='id', unique=False, **kwargs):
        super(ForeignKey, self).__init__(**kwargs)

        self.unique = unique  # TODO: handle unique FKs (O2O)
        self.target = target
        self.field = field

    def generate(self):
        target = self.blueprint[self.target]

        while True:
            # TODO: Support other types than AutoIncrement
            yield random.randint(0, target.total - 1)


