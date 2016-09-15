from collections import deque, OrderedDict


class Buffer(object):

    def __init__(self, blueprint, maxlen=1000):
        self.blueprint = blueprint
        self.backend = blueprint.backend
        self.maxlen = maxlen
        self.buffers = OrderedDict()

    def add(self, obj):
        item_name = type(obj).__name__
        buffer = self.get_buffer(item_name)
        buffer.append(obj)

        if len(buffer) == self.maxlen:
            self.write(item_name, buffer)

    def flush(self):
        while any(self.buffers.values()):
            for item_name, buffer in self.buffers.items():
                if buffer:
                    self.write(item_name, buffer)

    def write(self, item_name, buffer):
        item = self.blueprint.items[item_name]
        self.backend.write(item, tuple(item.db_values(obj) for obj in buffer))
        item.generate_dependencies(self, buffer)
        buffer.clear()

    def get_buffer(self, item_name):
        try:
            return self.buffers[item_name]
        except KeyError:
            buffer = deque(maxlen=self.maxlen)
            self.buffers[item_name] = buffer
            return buffer
