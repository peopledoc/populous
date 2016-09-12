import random

from .base import Generator


class Boolean(Generator):

    def generate(self):
        while True:
            yield random.random() >= 0.5
