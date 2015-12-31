from faker import Factory

fake = Factory.create()


class Generator(object):
    def __init__(self, nullable=False):
        self.nullable = nullable

    def next(self, populator, **kwargs):
        raise NotImplementedError
