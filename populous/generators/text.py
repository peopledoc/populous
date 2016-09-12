import itertools
import random
import string

from .base import Generator


class Text(Generator):

    def get_arguments(self, min_length=0, max_length=None, **kwargs):
        super(Text, self).get_arguments(**kwargs)

        self.min_length = min_length or 0
        self.max_length = max_length or 10000

    def letters(self):
        while True:
            yield random.choice(string.printable)

    def generate(self):
        letters = self.letters()

        while True:
            yield ''.join(
                itertools.islice(
                    letters, random.randint(self.min_length, self.max_length)
                )
            )
