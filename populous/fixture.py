from populous.factory import ItemFactory
from populous.vars import Expression
from populous.vars import parse_vars


class Fixture(object):

    def __init__(self, blueprint, item, name, params):
        self.blueprint = blueprint
        self.backend = blueprint.backend
        self.item = item
        self.name = name
        self.params = params

    def generate(self, buffer):
        print "# Generating", self.name
        try:
            item = self.blueprint.items[self.item]
        except KeyError:
            # TODO
            raise

        factory = ItemFactory(item)
        for field, value in self.params.items():
            value = parse_vars(value)
            factory.set(field, self.evaluate(value))

        self.blueprint.vars['this'] = factory
        obj = factory.generate()
        del self.blueprint.vars['this']

        keys = tuple(name for name in self.params.keys()
                     if name in item.db_fields)
        id_ = self.backend.upsert(item, keys, obj)
        obj = obj._replace(id=id_)

        self.blueprint.vars[self.name] = obj

        # TODO: write the batch when all the fixtures for this item
        #       have been generated
        item.batch_written(buffer, (obj,))

    def evaluate(self, value):
        if isinstance(value, Expression):
            return value.evaluate(**self.blueprint.vars)
        return value
