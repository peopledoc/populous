import random

from .base import Generator


class Integer(Generator):

    def get_arguments(self, min=0, max=(2 ** 32) - 1, **kwargs):
        super(Integer, self).get_arguments(**kwargs)

        self.min = min
        self.max = max

    def generate(self):
        while True:
            yield random.randint(self.min, self.max)
