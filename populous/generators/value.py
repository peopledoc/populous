from .base import Generator
from .vars import parse_vars

class Value(Generator):

    def get_arguments(self, value=None, **kwargs):
        super(Value, self).get_arguments(**kwargs)

        self.value = parse_vars(value)

    def generate(self):
        while True:
            yield self.evaluate(self.value)
