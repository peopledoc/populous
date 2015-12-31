import itertools
import random
import string

from .base import Generator


class Text(Generator):

    def __init__(self, min_length=0, max_length=None, **kwargs):
        super(Text, self).__init__(**kwargs)

        self.min_length = min_length or 0
        self.max_length = max_length or 10000

    @property
    def letters(self):
        while True:
            yield random.choice(string.printable)

    def next(self, *args, **kwargs):
        return ''.join(
            itertools.islice(
                self.letters, random.randint(self.min_length, self.max_length)
            )
        )
