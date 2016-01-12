import random

from .base import Generator


class Boolean(Generator):

    def __init__(self, **kwargs):
        super(Boolean, self).__init__(**kwargs)

    def generate(self):
        while True:
            yield random.random() >= 0.5
