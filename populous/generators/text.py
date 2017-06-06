import array
import os
import random

from string import ascii_lowercase
from string import ascii_uppercase
from string import digits
from string import printable
from string import punctuation

from populous.compat import ascii_letters

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
            '<a-Z>': ascii_letters,
            '<a-z>': ascii_lowercase,
            '<A-Z>': ascii_uppercase,
            '<0-9>': digits,
            '<spaces>': ' \t',
            '<printable>': printable,
            '<punctuation>': punctuation,
            '<newline>': '\n',
        }
        for category, chars in categories.items():
            description = description.replace(category, chars)

        return description

    def generate(self):
        chars = self.chars
        nb_chars = len(chars)

        while True:
            # get a random length for the string
            length = random.randint(self.min_length, self.max_length)
            # get a random array of short integers of the same length than
            # the final string
            rand_shorts = array.array('H', os.urandom(length * 2))
            # for each short in the array, get an element from the list
            # of possible chars
            yield ''.join([chars[short % nb_chars] for short in rand_shorts])
