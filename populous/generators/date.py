import random
from datetime import date
from datetime import datetime
from time import mktime, gmtime

from dateutil.parser import parse as dateutil_parse
from dateutil.tz import tzlocal

from .base import Generator


def to_timestamp(dt):
    if getattr(dt, 'tzinfo', None) is not None:
        dt = dt.astimezone(tzlocal())
    return mktime(dt.timetuple())


def parse_datetime(candidate):
    if isinstance(candidate, (datetime, date)):
        return candidate
    if isinstance(candidate, int):
        # we just assume this is a year
        candidate = str(candidate)
        # force the date to start at the 1st of January otherwise
        # dateutil takes the current day & month
        candidate = '01/01/' + candidate
    return dateutil_parse(candidate)


class DateTime(Generator):

    epoch_year = gmtime(0).tm_year

    def get_arguments(self, past=True, future=False, after=None, before=None,
                      **kwargs):
        super(DateTime, self).get_arguments(**kwargs)

        self.past = past
        self.future = future
        self.after = self.parse_vars(after)
        self.before = self.parse_vars(before)

    def generate(self):
        if not self.past:
            start = to_timestamp(datetime.now())
        else:
            # try not to go too far in the past
            start = to_timestamp(datetime(self.epoch_year, 1, 1))

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
