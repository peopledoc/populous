from peloton_bloomfilters import BloomFilter as _BloomFilter


class BloomFilter(object):

    def __init__(self, step=10000, errors=0.001):
        self._step = step
        self._errors = errors
        self._filters = [self._create_filter()]
        self._counter = 0

    def add(self, value, check=True):
        if check and value in self:
            return

        self._counter += 1
        if self._counter >= self._step:
            self._filters.append(self._create_filter())
            self._counter = 0

        f = self._filters[-1]
        f.add(value)

    def __contains__(self, value):
        for f in self._filters:
            if value in f:
                return True
        return False

    def _create_filter(self):
        return _BloomFilter(self._step, self._errors)
