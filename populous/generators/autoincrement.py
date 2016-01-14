from itertools import count

from .base import Generator


class AutoIncrement(Generator):

    def __init__(self, start=None, **kwargs):
        super(AutoIncrement, self).__init__(**kwargs)

        self._start = start

    @property
    def start(self):
        if self._start is None:
            backend = self.blueprint.backend
            value = backend.get_max_existing_value(self.item, self.field_name)
            self._start = value + 1 if value is not None else 1

        return self._start

    def generate(self):
        for i in count(self.start):
            yield i
