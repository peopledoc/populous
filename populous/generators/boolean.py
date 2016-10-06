import random

from .base import Generator


class Boolean(Generator):

    def get_arguments(self, ratio=0.5, **kwargs):
        super(Boolean, self).get_arguments(**kwargs)

        self.ratio = ratio

    def generate(self):
        while True:
            yield random.random() <= self.ratio
