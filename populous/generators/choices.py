import random
from operator import attrgetter

from .base import Generator


class Choices(Generator):

    def get_arguments(self, choices=(), **kwargs):
        super(Choices, self).get_arguments(**kwargs)

        if isinstance(choices, str):
            self.from_var = True
            self.var, _, attrs = choices.partition('.')
            if attrs:
                self.attrgetter = attrgetter(attrs)
            else:
                self.attrgetter = None
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
        var = self.blueprint.vars[self.var]
        if self.attrgetter:
            choices = self.attrgetter(var)
        else:
            choices = var
        return random.choice(choices)
