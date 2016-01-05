from .base import Generator, fake


class DateTime(Generator):

    def generate(self):
        while True:
            yield fake.date_time()


class Date(DateTime):

    def generate(self):
        for dt in super(Date, self).generate():
            yield dt.date()


class Time(DateTime):

    def generate(self):
        for dt in super(Date, self).generate():
            yield dt.time()
