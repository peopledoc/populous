import random
from datetime import datetime
from time import mktime

from dateutil.parser import parse as dateutil_parse
from dateutil.tz import tzlocal

from .base import Generator
from .vars import parse_vars


def to_timestamp(dt):
    if getattr(dt, 'tzinfo', None) is not None:
        dt = dt.astimezone(tzlocal())
    return mktime(dt.timetuple())


def parse_datetime(candidate):
    if isinstance(candidate, datetime):
        return candidate
    return dateutil_parse(candidate)


class DateTime(Generator):

    def get_arguments(self, past=True, future=False, after=None, before=None,
                      **kwargs):
        super(DateTime, self).get_arguments(**kwargs)

        self.past = past
        self.future = future
        self.after = parse_vars(after)
        self.before = parse_vars(before)

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

        if self.before:
            stop = to_timestamp(parse_datetime(self.evaluate(self.before)))

        if self.after:
            start = to_timestamp(parse_datetime(self.evaluate(self.after)))

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
