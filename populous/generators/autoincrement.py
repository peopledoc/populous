from itertools import count

from .base import Generator


class AutoIncrement(Generator):

    def __init__(self, start=0, **kwargs):
        super(AutoIncrement, self).__init__(**kwargs)

        self.start = start
        self.count = count(self.start)

    def next(self, *args, **kwargs):
        return next(self.count)
