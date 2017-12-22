from collections import deque, OrderedDict


class Buffer(object):

    def __init__(self, blueprint, maxlen=1000):
        self.blueprint = blueprint
        self.backend = blueprint.backend
        self.maxlen = maxlen
        self.buffers = OrderedDict(
            (item.name, deque(maxlen=self.maxlen))
            for item in self.blueprint.items.values()
        )

    def add(self, obj):
        item = self.blueprint.items[type(obj).__name__]
        buffer = self.buffers[item.name]
        buffer.append(obj)

        if len(buffer) == self.maxlen:
            self.write(item, buffer)

    def flush(self):
        while any(self.buffers.values()):
            for item_name, buffer in self.buffers.items():
                self.write(self.blueprint.items[item_name], buffer)

    def write(self, item, buffer=None):
        buffer = buffer or self.buffers[item.name]
        if not buffer:
            return
        ids = self.backend.write(
            item, tuple(item.db_values(obj) for obj in buffer)
        )
        item.batch_written(self, buffer, ids)
        buffer.clear()
