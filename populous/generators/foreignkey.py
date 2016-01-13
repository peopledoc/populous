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
        field = target.get_field(self.field)

        start = field.generator.start
        stop = start + target.total

        if self.item.count.by == self.target:
            pks = chain.from_iterable(
                repeat(pk, self.item.count.number)
                for pk in xrange(start, stop)
            )

            for pk in pks:
                yield pk
        else:
            while True:
                yield random.randint(start,  stop - 1)
