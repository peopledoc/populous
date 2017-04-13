from .base import Generator


class Value(Generator):

    def get_arguments(self, value=None, **kwargs):
        super(Value, self).get_arguments(**kwargs)

        self.value = self.parse_vars(value)

    def generate(self):
        while True:
            yield self.evaluate(self.value)
