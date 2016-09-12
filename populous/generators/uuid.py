from __future__ import absolute_import

import uuid

from .base import Generator


class UUID(Generator):

    def get_arguments(self, to_string=False, **kwargs):
        super(UUID, self).get_arguments(**kwargs)

        self.to_string = to_string

    def generate(self):
        if self.to_string:
            return (str(u) for u in self._generate())

        return self._generate()

    def _generate(self):
        while True:
            yield uuid.uuid4()
