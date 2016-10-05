

class ItemFactory(object):

    def __init__(self, item, parent=None):
        self.item = item
        self.blueprint = item.blueprint
        self._generated = {}

        if parent:
            self._generated[item.count.by] = parent

    def __getattribute__(self, name):
        try:
            return super(ItemFactory, self).__getattribute__(name)
        except AttributeError:
            generated = self._generated

            if name in generated:
                return generated[name]
            elif name in self.item.fields:
                value = self._get_value(name)
                generated[name] = value
                return value
            else:
                raise

    def generate(self):
        obj = self.item.namedtuple._make(
            getattr(self, name) for name in self.item.namedtuple._fields
        )
        self.clear()
        return obj

    def clear(self):
        parent = self.item.count.by
        if parent:
            self._generated = {parent: self._generated[parent]}
        else:
            self._generated = {}

    def _get_value(self, name):
        return next(self.item.fields[name])
