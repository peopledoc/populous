from collections import namedtuple

ITEM_ATTRIBUTES = ('name', 'table', 'count', 'fields')
COUNT_ATTRIBUTES = ('number', 'by')
FIELD_ATTRIBUTES = ('name', 'generator', 'params')


class ValidationError(Exception):
    pass


class Blueprint(object):

    def __init__(self, items=None):
        self.items = items or {}

        self.check_circular_dependencies()

    @classmethod
    def from_description(cls, description):
        if not isinstance(description, dict):
            raise ValidationError("You must describe the items as a "
                                  "dictionary (got: {})"
                                  .format(type(description)))

        def _load_item(name, attrs):
                try:
                    return Item.load(name, attrs)
                except ValidationError as e:
                    raise ValidationError("Error loading item '{}': {}"
                                          .format(name, e))

        return cls({
            name: _load_item(name, attrs)
            for name, attrs in description.items()
        })

    def __iter__(self):
        for item in self.items.values():
            yield item

    def __getitem__(self, key):
        try:
            return self.items[key]
        except KeyError:
            raise ValidationError("The item '{}' was not found in the "
                                  "blueprint".format(self.by))

    def get_total_for(self, name):
        item = self[name]

        if not item.count.by:
            return item.count.number
        else:
            return self.get_total_for(item.count.by) * item.count.number

    def check_circular_dependencies(self):

        def _check_ancestors(current, ancestors):
            parent = current.count.by

            if not parent:
                return

            if parent in ancestors:
                raise ValueError("Circular dependency between {} and {}"
                                 .format(current.name, parent))

            ancestors.add(current.name)
            _check_ancestors(self[parent], ancestors)

        for item in self:
            _check_ancestors(item, set())


class Item(namedtuple('Item', ITEM_ATTRIBUTES)):
    __slots__ = ()

    @classmethod
    def load(cls, name, attrs):
        if not isinstance(attrs, dict):
            raise ValidationError("Blueprint items must be dictionaries "
                                  "(got: {})".format(type(attrs)))

        table = attrs.pop('table', None)

        if not table:
            raise ValidationError("Blueprint items must have a table")

        fields = attrs.pop('fields', {})

        if not isinstance(fields, dict):
            raise ValidationError("Fields description must be a dictionary "
                                  "(got: {})".format(type(fields)))

        count = attrs.pop('count', 0)

        if attrs:
            raise ValidationError("Blueprint item got unexpected arguments: {}"
                                  .format(', '.join(attrs.keys())))

        return cls(
            name=name,
            table=table,
            count=Count.load(count),
            fields=tuple(
                Field.load(name, desc) for name, desc in fields.items()
            ),
        )


class Count(namedtuple('Count', COUNT_ATTRIBUTES)):
    __slots__ = ()

    @classmethod
    def load(cls, attrs):
        if isinstance(attrs, int):
            attrs = {'number': attrs}
        elif not isinstance(attrs, dict):
            raise ValidationError("The 'count' attribute must be either an "
                                  "integer or a dictionary (got: {})"
                                  .format(type(attrs)))

        number = attrs.pop('number', 0)

        if not isinstance(number, int):
            raise ValidationError("A count must be an integer (got: {})"
                                  .format(type(number)))
        elif number < 0:
            raise ValidationError("A count must be a positive number (got: {})"
                                  .format(number))

        by = attrs.pop('by', None)

        if by is not None and not isinstance(by, str):
            raise ValidationError("The 'by' attribute of 'count' must be a "
                                  "string (got: {})".format(type(by)))

        if attrs:
            raise ValidationError("'count' attribute got unexpected arguments"
                                  ": {}".format(', '.join(attrs.keys())))

        return cls(number=number, by=by)


class Field(namedtuple('Field', FIELD_ATTRIBUTES)):
    __slots__ = ()

    @classmethod
    def load(cls, name, attrs):
        if not isinstance(attrs, dict):
            raise ValidationError("A field description must be a dictionary "
                                  "(got: {})".format(type(attrs)))

        generator = attrs.pop('generator', None)

        if not isinstance(generator, str):
            raise ValidationError("The generator in a field description must "
                                  "be a string (got: {})"
                                  .format(type(generator)))

        params = attrs.pop('params', {})

        if not isinstance(params, dict):
            raise ValidationError("The params of a field generator must be a "
                                  "dictionary (got: {})".format(type(params)))

        if attrs:
            raise ValidationError("Field descrption got unexpected arguments: "
                                  "{}".format(', '.join(attrs.keys())))

        return cls(name=name, generator=generator, params=params)
