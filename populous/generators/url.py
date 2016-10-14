from .base import Generator, fake


class URL(Generator):

    def generate(self):
        while True:
            yield fake.url().rstrip('/')
