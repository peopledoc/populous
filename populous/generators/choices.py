import random

from .base import Generator
from .vars import parse_vars


class Choices(Generator):

    def get_arguments(self, choices=(), **kwargs):
        super(Choices, self).get_arguments(**kwargs)

        if isinstance(choices, str):
            self.from_var = True
            self.choices = parse_vars(choices)
        else:
            self.from_var = False
            self.choices = choices

    def generate(self):
        if self.from_var:
            generator = self._generate_from_var
        else:
            generator = self._generate_from_list

        while True:
            yield generator()

    def _generate_from_list(self):
        return self.evaluate(random.choice(self.choices))

    def _generate_from_var(self):
        return random.choice(self.evaluate(self.choices))
