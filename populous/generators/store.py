from .base import Generator


class Store(Generator):

    def get_arguments(self, **kwargs):
        kwargs['shadow'] = True
        super().get_arguments(**kwargs)

    def generate(self):
        while True:
            yield []
