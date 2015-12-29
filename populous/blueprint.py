from collections import namedtuple

ITEM_ATTRIBUTES = ('table', 'count', 'fields')
COUNT_ATTRIBUTES = ('number', 'by')
FIELD_ATTRIBUTES = ('generator', 'params')


class ValidationError(Exception):
    pass


class Blueprint(object):

    def __init__(self, items):
        self.items = items

    @classmethod
    def from_description(cls, description):
        items = {}

        if not isinstance(description, dict):
            raise ValidationError("You must describe the items as a "
                                  "dictionary (got: {})"
                                  .format(type(description)))

        for name, attrs in description.items():
            try:
                items[name] = Item.load(attrs)
            except ValidationError as e:
                raise ValidationError("Error loading item '{}': {}"
                                      .format(name, e))

        return cls(items)


class Item(namedtuple('Item', ITEM_ATTRIBUTES)):

    @classmethod
    def load(cls, attrs):
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
            table=table,
            count=Count.load(count),
            fields={
                name: Field.load(desc) for name, desc in fields.items()
            },
        )


class Count(namedtuple('Count', COUNT_ATTRIBUTES)):

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

        return cls(
            number=number,
            by=by,
        )


class Field(namedtuple('Field', FIELD_ATTRIBUTES)):

    @classmethod
    def load(cls, attrs):
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

        return cls(
            generator=generator,
            params=params
        )
