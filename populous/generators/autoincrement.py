from itertools import count

from .base import Generator


class AutoIncrement(Generator):

    def __init__(self, start=None, **kwargs):
        super(AutoIncrement, self).__init__(**kwargs)

        self._start = start

    @property
    def start(self):
        if self._start is None:
            self._start = self._get_start()

        return self._start

    def _get_start(self):
        backend = self.blueprint.backend

        if not backend:
            return 0

        value = backend.get_max_existing_value(self.item, self.field_name)
        return value + 1 if value is not None else 0

    def generate(self):
        for i in count(self.start):
            yield i
