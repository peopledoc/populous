import random

from itertools import chain, repeat

from .base import Generator


class ForeignKey(Generator):

    def __init__(self, target=None, field='id', unique=False, **kwargs):
        super(ForeignKey, self).__init__(**kwargs)

        self.unique = unique  # TODO: handle unique FKs (O2O)
        self.target = target
        self.field = field

    def generate(self):
        target = self.blueprint[self.target]

        if self.item.count.by == self.target:
            pks = chain.from_iterable(
                repeat(pk, self.item.count.number)
                for pk in xrange(0, target.total)
            )

            for pk in pks:
                yield pk
        else:
            while True:
                # TODO: Support other types than AutoIncrement
                yield random.randint(0, target.total - 1)
