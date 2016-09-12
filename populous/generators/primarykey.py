from itertools import count

from .base import Generator


class IntegerPrimaryKey(Generator):

    def get_arguments(self, step=1, **kwargs):
        super(IntegerPrimaryKey, self).get_arguments(**kwargs)

        self.step = step
        self.shadow = True

    def generate(self):
        backend = self.blueprint.backend
        next_pk = backend.get_next_pk(self.item, self.field_name)
        start = next_pk if next_pk is not None else 1

        return count(start, step=self.step)
