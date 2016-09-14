from .base import Generator, fake


class Email(Generator):

    def generate(self):
        while True:
            yield fake.email()
