from .base import Generator, fake


class DateTime(Generator):

    def next(self, *args, **kwargs):
        return fake.date_time()


class Date(DateTime):

    def next(self, *args, **kwargs):
        return super(Date, self).next().date()


class Time(DateTime):

    def next(self, *args, **kwargs):
        return super(Time, self).next().time()
