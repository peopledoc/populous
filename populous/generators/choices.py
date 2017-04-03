import random

from populous.exceptions import GenerationError

from .base import Generator


class Choices(Generator):

    def get_arguments(self, choices=(), **kwargs):
        super(Choices, self).get_arguments(**kwargs)

        if isinstance(choices, str):
            self.from_var = True
            self.choices = self.parse_vars(choices)
        else:
            self.from_var = False
            self.choices = choices

    def generate(self):
        if self.from_var:
            generator = self._generate_from_var
        else:
            if not self.choices:
                raise GenerationError(
                    "The choices for field '{}' of item '{}' are empty."
                    .format(self.field_name, self.item.name)
                )
            generator = self._generate_from_list

        while True:
            yield generator()

    def _generate_from_list(self):
        return self.evaluate(random.choice(self.choices))

    def _generate_from_var(self):
        try:
            return random.choice(self.evaluate(self.choices))
        except IndexError:
            if self.nullable:
                return None
            raise GenerationError(
                "The choices for field '{}' of item '{}' are empty, and "
                "the field is not nullable."
                .format(self.field_name, self.item.name)
            )
