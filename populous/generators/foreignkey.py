import random

from .base import Generator


class ForeignKey(Generator):

    def __init__(self, target=None, field='id', unique=False, **kwargs):
        super(ForeignKey, self).__init__(**kwargs)

        self.unique = unique  # TODO: handle unique FKs (O2O)
        self.target = target
        self.field = field

    def next(self, populator, lazy=True, **kwargs):
        try:
            instance = kwargs[self.target]
        except KeyError:
            objects = populator.get(self.target)
            instance = random.choice(objects)

        return getattr(instance, self.field)
