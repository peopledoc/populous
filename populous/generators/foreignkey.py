import random

from itertools import chain, repeat

from .base import Generator


class ForeignKey(Generator):

    def __init__(self, target=None, field='id', unique=False, **kwargs):
        super(ForeignKey, self).__init__(**kwargs)

        self.unique = unique  # TODO: handle unique FKs (O2O)
        self.target = self.blueprint[target]
        self.field = field  # TODO: handle other field types than AutoIncrement

        backend = self.blueprint.backend
        next_pk = backend.get_next_pk(self.target, self.field)
        self.start = next_pk if next_pk is not None else 1
        self.stop = self.start + self.target.total

    def generate(self):
        if self.item.count.by == self.target.name:
            pks = chain.from_iterable(
                repeat(pk, self.item.count.number)
                for pk in xrange(self.start, self.stop)
            )

            for pk in pks:
                yield pk
        else:
            while True:
                yield random.randint(self.start,  self.stop - 1)
