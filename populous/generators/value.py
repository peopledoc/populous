from .base import Generator


class Value(Generator):

    def __init__(self, value=None, **kwargs):
        super(Value, self).__init__(**kwargs)

        self.value = value

    def generate(self):
        while True:
            yield self.value
