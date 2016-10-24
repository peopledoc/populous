import itertools
import random
import string

from .base import Generator


class Text(Generator):

    def get_arguments(self, min_length=0, max_length=None, chars='<a-Z><0-9> ',
                      **kwargs):
        super(Text, self).get_arguments(**kwargs)

        self.min_length = min_length or 0
        self.max_length = max_length or 10000
        self.chars = self.get_chars(chars)

    def get_chars(self, description):
        categories = {
            '<a-Z>': string.ascii_letters,
            '<a-z>': string.ascii_lowercase,
            '<A-Z>': string.ascii_uppercase,
            '<0-9>': string.digits,
            '<spaces>': ' \t',
            '<printable>': string.printable,
            '<punctuation>': string.punctuation,
            '<newline>': '\n',
        }
        for category, chars in categories.items():
            description = description.replace(category, chars)

        return description

    def generate(self):
        def _chars():
            while True:
                yield random.choice(self.chars)
        chars = _chars()

        while True:
            yield ''.join(
                itertools.islice(
                    chars, random.randint(self.min_length, self.max_length)
                )
            )
