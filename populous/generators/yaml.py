from __future__ import absolute_import

import yaml

from populous.exceptions import GenerationError
from .base import Generator


class Yaml(Generator):

    def get_arguments(self, value=None, to_json=False, **kwargs):
        super(Yaml, self).get_arguments(**kwargs)

        self.value = self.parse_vars(value)
        self.to_json = to_json

    def generate(self):
        if self.to_json:
            return self._generate_to_json()

        return self._generate()

    def _generate(self):
        while True:
            try:
                yield yaml.load(self.evaluate(self.value))
            except yaml.YAMLError as e:
                raise GenerationError(
                    "Item '{}', field '{}': Invalid YAML: {}"
                    .format(self.item.name, self.field_name, e)
                )

    def _generate_to_json(self):
        convert = self.blueprint.backend.json_adapter
        for value in self._generate():
            yield convert(value)
