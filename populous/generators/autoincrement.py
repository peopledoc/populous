from itertools import count

from .base import Generator


class AutoIncrement(Generator):

    def __init__(self, start=0, **kwargs):
        super(AutoIncrement, self).__init__(**kwargs)

        self.start = start

    def generate(self):
        for i in count(self.start):
            yield i
