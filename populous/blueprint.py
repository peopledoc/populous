import logging

from collections import OrderedDict, defaultdict

from populous.bloom import BloomFilter
from populous.buffer import Buffer
from populous.compat import basestring
from populous.exceptions import ValidationError
from populous.item import Item, COUNT_KEYS, ITEM_KEYS


logger = logging.getLogger('populous')


class Blueprint(object):

    def __init__(self, items=None, vars_=None, backend=None):
        self.items = OrderedDict(items or {})
        self.vars = vars_ or {}
        self.backend = backend

        # a dict containing {<table>: {<fields>: bloom filter}}
        # to store the existing values of unique fields
        self.seen = defaultdict(lambda: defaultdict(BloomFilter))

    def add_var(self, name, value):
        self.vars[name] = value

    def add_item(self, description):
        if not isinstance(description, dict):
            raise ValidationError(
                "A blueprint item must be a dict, not a '{}'"
                .format(type(description).__name__)
            )

        if any(key not in ITEM_KEYS for key in description.keys()):
            extra = set(description.keys()) - set(ITEM_KEYS)
            raise ValidationError(
                "Unknown key(s) '{}'. Possible keys are '{}'."
                .format(', '.join(extra), ', '.join(ITEM_KEYS))
            )

        name = description.pop('name', None)
        parent = None
        if name and name in self.items:
            # this item already exists, this mean we are trying
            # to override it
            if description.get('parent', name) != name:
                raise ValidationError(
                    "Re-defining item '{}' while setting '{}' as parent "
                    "is ambiguous.".format(name, description['parent'])
                )
            description['parent'] = name

        if description.get('parent'):
            parent_name = description['parent']
            if parent_name not in self.items:
                raise ValidationError(
                    "Parent '{}' does not exist.".format(parent_name)
                )
            parent = self.items[parent_name]
            if not name:
                name = parent.name

        store_in = description.get('store_in')
        if store_in:
            if not isinstance(store_in, dict):
                raise ValidationError(
                    "'store_in' must be a dict, not a '{}'"
                    .format(type(store_in).__name__)
                )

        item = Item(
            blueprint=self, name=name, table=description.get('table'),
            parent=parent, store_in=store_in
        )

        fields = description.get('fields', {})
        if not isinstance(fields, dict):
            raise ValidationError(
                "Fields must be a dict, not a '{}'"
                .format(type(fields).__name__)
            )
        for field_name, attrs in fields.items():
            if isinstance(attrs, dict):
                generator = attrs.pop('generator', None)
                params = attrs
            else:
                # If we didn't get a dict, this is a fixed value
                generator = 'Value'
                params = {'value': attrs}

            item.add_field(field_name, generator, **params)

        count = description.get('count')
        if count is None:
            pass
        elif isinstance(count, int):
            item.add_count(number=count)
        elif isinstance(count, basestring) and count[0] == '$':
            item.add_count(number=count)
        else:
            if not isinstance(count, dict):
                raise ValidationError(
                    "The count of item '{}' must be an integer or a dict."
                    .format(name)
                )

            if any(key not in COUNT_KEYS for key in count.keys()):
                extra = set(count.keys()) - set(COUNT_KEYS)
                raise ValidationError(
                    "Unknown key(s) '{}' in count of item '{}'. Possible "
                    "keys are '{}'."
                    .format(', '.join(extra), name, ', '.join(COUNT_KEYS))
                )

            item.add_count(**count)

        self.items[name] = item

    def preprocess(self):
        for item in self.items.values():
            item.preprocess()

    def generate(self):
        logger.info("Getting existing unique values...")

        self.preprocess()

        buffer = Buffer(self)

        logger.info("Starting generation...")

        for item in self.items.values():
            if item.count.by:
                # we only create the items with no dependency,
                # the others will be created on the fly
                continue

            item.generate(buffer, item.count())

        # write everything left in the buffer
        buffer.flush()

        logger.info("Generation done.")
