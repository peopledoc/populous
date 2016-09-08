

class ItemFactory(object):

    def __init__(self, item):
        self.item = item
        self.blueprint = item.blueprint
        self._generated = {}

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
        self.blueprint.vars['this'] = self
        values = self.item.namedtuple._make(
            getattr(self, name) for name in self.item.namedtuple._fields
        )
        del self.blueprint.vars['this']
        return values

    def _get_value(self, name):
        return next(self.item.fields[name])
