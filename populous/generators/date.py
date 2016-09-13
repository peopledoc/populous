import random
from datetime import datetime
from time import mktime

from dateutil.tz import tzlocal

from .base import Generator


def to_timestamp(dt):
    if getattr(dt, 'tzinfo', None) is not None:
        dt = dt.astimezone(tzlocal())
    return mktime(dt.timetuple())


class DateTime(Generator):

    def get_arguments(self, past=True, future=False, **kwargs):
        super(DateTime, self).get_arguments(**kwargs)

        self.past = past
        self.future = future

    def generate(self):
        if not self.past:
            start = to_timestamp(datetime.now())
        else:
            # try not to go too far in the past
            start = to_timestamp(datetime(1900, 1, 1))

        if self.future:
            # try not to go too far in the future
            stop = to_timestamp(datetime(2100, 1, 1))
        else:
            stop = to_timestamp(datetime.now())

        while True:
            yield datetime.fromtimestamp(
                random.randint(start, stop)
            )


class Date(DateTime):

    def generate(self):
        for dt in super(Date, self).generate():
            yield dt.date()


class Time(DateTime):

    def generate(self):
        for dt in super(DateTime, self).generate():
            yield dt.time()
