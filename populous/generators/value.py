from .base import Generator


class Value(Generator):

    def get_arguments(self, value=None, to_json=False, **kwargs):
        super(Value, self).get_arguments(**kwargs)

        self.value = self.parse_vars(value)
        self.to_json = to_json

    def generate(self):
        if self.to_json:
            return self._generate_to_json()

        return self._generate()

    def _generate(self):
        while True:
            yield self.evaluate(self.value)

    def _generate_to_json(self):
        convert = self.blueprint.backend.json_adapter
        for value in self._generate():
            yield convert(value)
