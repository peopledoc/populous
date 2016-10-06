from populous.exceptions import ValidationError

from .base import Generator, fake


class Name(Generator):

    def get_arguments(self, gender=None, max_length=None, **kwargs):
        super(Name, self).get_arguments(**kwargs)

        self.gender = self.parse_vars(gender)
        self.max_length = max_length

    def _get_provider(self):
        gender = self.evaluate(self.gender)

        if gender not in ('M', 'F', None):
            raise ValidationError(
                "Gender must be either 'M', 'F' or null. Got '{}'"
                .format(gender)
            )

        if gender == 'F':
            return fake.name_female
        elif gender == 'M':
            return fake.name_male
        else:
            return fake.name

    def generate(self):
        provider = self._get_provider()
        while True:
            value = provider()
            if self.max_length and len(value) > self.max_length:
                continue
            yield value


class FirstName(Name):

    def _get_provider(self):
        if self.gender == 'F':
            return fake.first_name_female
        elif self.gender == 'M':
            return fake.first_name_male
        else:
            return fake.first_name


class LastName(Generator):

    def get_arguments(self, max_length=None, **kwargs):
        super(LastName, self).get_arguments(**kwargs)

        self.max_length = max_length

    def generate(self):
        while True:
            name = fake.last_name()
            if self.max_length and len(name) > self.max_length:
                continue
            yield name
