import peloton_bloomfilters as bloomfilter


class BloomFilter(object):

    def __init__(self, capacity=1000, error_rate=0.000001):
        self._capacity = capacity
        self._error_rate = error_rate
        self._filters = []
        self._counter = 0
        self._filters.append(self._create_filter())

    def add(self, value, check=True):
        if check and value in self:
            return

        self._counter += 1
        if self._counter >= self._capacity:
            self._filters.append(self._create_filter())
            self._counter = 1

        f = self._filters[-1]
        f.add(value)

    def __contains__(self, value):
        for f in reversed(self._filters):
            if value in f:
                return True
        return False

    def _create_filter(self):
        if self._filters:
            self._capacity *= 4
            self._error_rate *= 0.9
        return bloomfilter.BloomFilter(self._capacity, self._error_rate)
