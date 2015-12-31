

class Populator(object):

    def __init__(self, blueprint):
        self.blueprint = blueprint
        self.objects = {}

    def populate(self):
        for item in self.blueprint:
            self.get(item.name)

    def get(self, name):
        try:
            return self.objects[name]
        except KeyError:
            pass

        objects = self.generate_all(self.blueprint[name])
        self.objects[name] = objects
        return objects

    def generate_all(self, item):
        parent = item.count.by

        if parent:
            return tuple(
                self.generate_one(item, **{parent: instance})
                for instance in self.get(parent)
                for _ in range(item.count.number)
            )
        else:
            return tuple(
                self.generate_one(item) for _ in range(item.count.number)
            )

    def generate_one(self, item, **kwargs):
        return item.row._make(
            field.generator.next(self, **kwargs)
            for field in item.fields
        )
