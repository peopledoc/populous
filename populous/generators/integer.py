import random

from .base import Generator


class Integer(Generator):

    def __init__(self, min=0, max=(2 ** 32) - 1, **kwargs):
        super(Integer, self).__init__(**kwargs)

        self.min = min
        self.stop = max

    def generate(self):
        while True:
            yield random.randint(self.min, self.max)
