import random

from .base import Generator


class Choices(Generator):

    def __init__(self, choices=(), **kwargs):
        super(Choices, self).__init__(**kwargs)

        self.choices = tuple(choices)

    def next(self, *args, **kwargs):
        return random.choice(self.choices)
