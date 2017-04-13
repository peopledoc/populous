import random

from populous.vars import parse_vars
from .base import Generator


class Integer(Generator):

    def get_arguments(self, min=0, max=(2 ** 32) - 1, to_string=False,
                      **kwargs):
        super(Integer, self).get_arguments(**kwargs)

        self.min = parse_vars(min)
        self.max = parse_vars(max)
        self.to_string = to_string

    def generate(self):
        if self.to_string:
            return (str(e) for e in self._generate())
        return self._generate()

    def _generate(self):
        while True:
            yield random.randint(
                self.evaluate(self.min),
                self.evaluate(self.max)
            )
