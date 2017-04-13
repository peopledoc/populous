import socket
from itertools import islice

import pytest

from populous.backends.base import Backend
from populous.exceptions import GenerationError
from populous.exceptions import ValidationError
from populous import generators
from populous.generators.base import NullableMixin
from populous.generators.base import UniquenessMixin


def take(generator, length=100):
    return list(islice(generator, length))


def validate_ip(ip, family='both'):
    def check(ip, family):
        try:
            socket.inet_pton(family, ip)
            return True
        except socket.error:
            return False

    if family in ('both', 'IPv4') and check(ip, socket.AF_INET):
        return True
    if family in ('both', 'IPv6') and check(ip, socket.AF_INET6):
        return True
    return False


@pytest.fixture
def blueprint():
    from populous.blueprint import Blueprint

    return Blueprint()


@pytest.fixture
def item(blueprint):
    blueprint.add_item({'name': 'item', 'table': 'table_foo'})
    return blueprint.items['item']


def test_base_generator_refuse_extra_argument(item):
    msg = ("Item 'item', field 'foo': Got extra param(s) for "
           "generator 'BaseGenerator': foo")
    with pytest.raises(ValidationError) as e:
        generators.BaseGenerator(item, 'foo', foo='bar')
    assert msg in e.value


def test_nullable(item):

    class DummyGenerator(NullableMixin, generators.BaseGenerator):
        def generate(self):
            from itertools import count
            return count()

    generator = DummyGenerator(item, 'foo', nullable=False)
    assert generator.nullable == 0
    assert None not in take(generator)

    generator = DummyGenerator(item, 'foo', nullable=True)
    assert generator.nullable == 0.5
    sample = take(generator, 1000)
    assert None in sample
    assert 1 in sample
    assert 200 < sample.count(None) < 800
    assert max(sample) == 1000 - sample.count(None) - 1

    generator = DummyGenerator(item, 'foo', nullable=0.1)
    sample = take(generator, 1000)
    assert None in sample
    assert 0 < sample.count(None) < 200
    assert max(sample) == 1000 - sample.count(None) - 1


def test_uniqueness(item):

    class DummyGenerator(UniquenessMixin, generators.BaseGenerator):
        def generate(self):
            while True:
                import random
                yield random.randint(0, 9)

    generator = DummyGenerator(item, 'foo', unique=True)
    assert sorted(take(generator, 10)) == list(range(10))

    msg = ("Item 'item', field 'foo': Could not generate a new unique "
           "value in 10000 tries. Aborting.")
    with pytest.raises(GenerationError) as e:
        take(generator, 11)
    assert msg in str(e.value)


def test_unique_together(blueprint, item):

    class DummyGenerator(UniquenessMixin, generators.BaseGenerator):
        def generate(self):
            while True:
                import random
                yield random.randint(0, 9)

    generator = DummyGenerator(item, 'foo', unique='bar')
    assert generator.unique is True
    assert generator.unique_with == ('bar',)

    class Item:
        def __init__(self, bar=None, lol=None):
            self.bar = bar
            self.lol = lol

    blueprint.vars['this'] = Item(bar=42)
    assert sorted(take(generator, 10)) == list(range(10))

    blueprint.vars['this'] = Item(bar='foo')
    assert sorted(take(generator, 10)) == list(range(10))

    generator = DummyGenerator(item, 'foo', unique=['bar', 'lol'])
    assert generator.unique is True
    assert generator.unique_with == ('bar', 'lol')

    blueprint.vars['this'] = Item(bar='test', lol=42)
    assert sorted(take(generator, 10)) == list(range(10))

    blueprint.vars['this'] = Item(bar='test', lol=None)
    assert sorted(take(generator, 10)) == list(range(10))

    msg = ("Item 'item', field 'foo': Could not generate a new unique "
           "value in 10000 tries. Aborting.")
    with pytest.raises(GenerationError) as e:
        take(generator, 11)
    assert msg in str(e.value)


def test_integer(blueprint, item):
    generator = generators.Integer(item, 'foo')
    sample = take(generator, 10)
    assert len(sample) == 10
    assert all(isinstance(e, int) for e in sample)

    generator = generators.Integer(item, 'foo', to_string=True)
    assert all(e.isdigit() for e in take(generator, 10))

    generator = generators.Integer(item, 'foo', min=10, max=100)
    assert all(10 <= e <= 100 for e in take(generator, 1000))

    generator = generators.Integer(item, 'foo', min='$min', max='$max')
    blueprint.vars['min'] = 10
    blueprint.vars['max'] = 20
    assert all(10 <= e <= 20 for e in take(generator, 100))
    blueprint.vars['min'] = 15
    assert all(15 <= e <= 20 for e in take(generator, 100))


def test_choices(blueprint, item):
    generator = generators.Choices(item, 'foo', choices=range(10))
    sample = take(generator, 100)
    assert len(sample) == 100
    assert all(e in range(10) for e in sample)

    generator = generators.Choices(item, 'foo', choices='$test')
    blueprint.vars['test'] = 'abcd'
    sample = take(generator, 10)
    assert len(sample) == 10
    assert all(e in 'abcd' for e in sample)

    blueprint.vars['test'] = 'xyz'
    sample = take(generator, 10)
    assert len(sample) == 10
    assert all(e in 'xyz' for e in sample)


def test_choices_empty(blueprint, item):
    generator = generators.Choices(item, 'foo', choices=[])
    with pytest.raises(GenerationError) as e:
        take(generator, 1)
    msg = "The choices for field 'foo' of item 'item' are empty."
    assert msg in str(e.value)

    generator = generators.Choices(item, 'foo', choices='$test')
    blueprint.vars['test'] = []

    generator.nullable = 0.5
    sample = take(generator, 10)
    assert sample == [None] * 10

    blueprint.vars['test'] = ['foo']
    assert take(generator, 1) == ['foo']

    blueprint.vars['test'] = []
    generator.nullable = 0
    with pytest.raises(GenerationError) as e:
        take(generator, 1)
    msg = ("The choices for field 'foo' of item 'item' are empty, and the "
           "field is not nullable.")
    assert msg in str(e.value)


def test_boolean(item):
    generator = generators.Boolean(item, 'foo')
    sample = take(generator, 100)
    assert len(sample) == 100
    assert all(e in (True, False) for e in sample)
    assert 20 < sample.count(True) < 80

    generator = generators.Boolean(item, 'foo', ratio=0.1)
    sample = take(generator, 100)
    assert len(sample) == 100
    assert all(e in (True, False) for e in sample)
    assert 0 <= sample.count(True) < 40


def test_select(blueprint, item):
    class DummyBackend():
        def select_random(self, *args, **kwargs):
            return [1, 2, 3]

    blueprint.backend = DummyBackend()

    generator = generators.Select(item, 'foo', table='test')
    assert take(generator, 5) == [1, 2, 3, 1, 2]

    generator = generators.Select(item, 'foo', table='test',
                                  where='foo={{ bar }}')
    blueprint.vars['bar'] = 1
    assert take(generator, 2) == [1, 2]
    blueprint.vars['bar'] = 2
    assert take(generator, 2) == [1, 2]


def test_value(blueprint, item):
    generator = generators.Value(item, 'foo', value=42)
    assert take(generator, 2) == [42, 42]

    generator = generators.Value(item, 'foo', value='foo')
    assert take(generator, 2) == ['foo', 'foo']

    generator = generators.Value(item, 'foo', value='$foo')
    blueprint.vars['foo'] = None
    assert take(generator, 2) == [None, None]
    blueprint.vars['foo'] = 'bar'
    assert take(generator, 2) == ['bar', 'bar']


def test_value_to_json(blueprint, item):
    blueprint.backend = Backend()
    generator = generators.Value(item, 'foo', value={'foo': 42}, to_json=True)
    assert take(generator, 2) == ['{"foo": 42}'] * 2

    class DummyBackend(Backend):
        @property
        def json_adapter(self):
            return lambda v: 'bar'

    blueprint.backend = DummyBackend()
    generator = generators.Value(item, 'foo', value={'foo': 42}, to_json=True)
    assert take(generator, 2) == ['bar', 'bar']


def test_email(item):
    generator = generators.Email(item, 'foo', unique=True)
    sample = take(generator, 10)
    assert len(sample) == 10
    assert all('@' in e for e in sample)
    assert len(set(sample)) == 10


def test_uuid(item):
    import uuid

    generator = generators.UUID(item, 'foo')
    sample = take(generator, 10)
    assert len(sample) == 10
    assert all(isinstance(e, uuid.UUID) for e in sample)
    assert len(set(sample)) == 10

    generator = generators.UUID(item, 'foo', to_string=True)
    sample = take(generator, 10)
    assert len(sample) == 10
    assert all(isinstance(e, str) for e in sample)
    assert all(uuid.UUID(e) for e in sample)
    assert len(set(sample)) == 10


def test_text(item):
    import string

    generator = generators.Text(item, 'foo')
    sample = take(generator, 10)
    assert len(sample) == 10
    assert all(isinstance(e, str) for e in sample)
    chars = string.letters + string.digits + ' '
    assert all(all(c in chars for c in e) for e in sample)

    generator = generators.Text(item, 'foo', min_length=10, max_length=100)
    assert all(10 <= len(e) <= 100 for e in take(generator, 10))

    generator = generators.Text(item, 'foo', chars='<0-9>', min_length=1,
                                max_length=100)
    sample = take(generator, 10)
    assert len(sample) == 10
    assert all(e.isdigit() for e in sample)

    generator = generators.Text(item, 'foo', chars='<printable>',
                                min_length=1, max_length=100)
    sample = take(generator, 10)
    assert len(sample) == 10
    assert all((c in string.printable for c in e) for e in sample)

    generator = generators.Text(item, 'foo', chars='<a-z><0-9>',
                                min_length=1, max_length=100)
    sample = take(generator, 10)
    assert len(sample) == 10
    chars = string.ascii_lowercase + string.digits
    assert all((c in chars for c in e) for e in sample)

    generator = generators.Text(item, 'foo', chars='abc', min_length=1,
                                max_length=100)
    sample = take(generator, 10)
    assert len(sample) == 10
    assert all((c in 'abc' for c in e) for e in sample)


def test_datetime(blueprint, item):
    from datetime import datetime

    generator = generators.DateTime(item, 'foo')
    sample = take(generator, 100)
    assert len(sample) == 100
    assert all(isinstance(e, datetime) for e in sample)
    assert all(e >= datetime(1900, 1, 1) for e in sample)
    assert all(e < datetime.now() for e in sample)

    generator = generators.DateTime(item, 'foo', future=True, past=False)
    sample = take(generator, 100)
    assert all(e >= datetime.now() for e in sample)
    assert all(e < datetime(2100, 1, 1) for e in sample)

    generator = generators.DateTime(item, 'foo', after=datetime(2012, 10, 10))
    sample = take(generator, 100)
    assert all(e >= datetime(2012, 10, 10) for e in sample)
    assert all(e <= datetime.now() for e in sample)

    generator = generators.DateTime(item, 'foo', after=datetime(2012, 10, 10),
                                    future=True)
    sample = take(generator, 100)
    assert all(e >= datetime(2012, 10, 10) for e in sample)
    assert all(e <= datetime(2100, 1, 1) for e in sample)

    generator = generators.DateTime(item, 'foo', before=datetime(2012, 10, 10))
    sample = take(generator, 100)
    assert all(e >= datetime(1900, 1, 1) for e in sample)
    assert all(e <= datetime(2012, 10, 10) for e in sample)

    generator = generators.DateTime(item, 'foo', before=datetime(2012, 10, 10),
                                    future=True)
    sample = take(generator, 100)
    assert all(e >= datetime(1900, 1, 1) for e in sample)
    assert all(e <= datetime(2012, 10, 10) for e in sample)

    generator = generators.DateTime(item, 'foo', after='$stop')
    blueprint.vars['stop'] = datetime(2012, 10, 10)
    sample = take(generator, 100)
    assert all(e >= datetime(2012, 10, 10) for e in sample)
    assert all(e <= datetime(2100, 1, 1) for e in sample)

    generator = generators.DateTime(item, 'foo', before='$start')
    blueprint.vars['start'] = datetime(2012, 10, 10)
    sample = take(generator, 100)
    assert all(e >= datetime(1900, 1, 1) for e in sample)
    assert all(e <= datetime(2012, 10, 10) for e in sample)


def test_date(blueprint, item):
    from datetime import date

    generator = generators.Date(item, 'foo')
    sample = take(generator, 100)
    assert len(sample) == 100
    assert all(isinstance(e, date) for e in sample)
    assert all(e >= date(1900, 1, 1) for e in sample)
    assert all(e < date.today() for e in sample)

    generator = generators.Date(item, 'foo', future=True, past=False)
    sample = take(generator, 100)
    assert all(e >= date.today() for e in sample)
    assert all(e < date(2100, 1, 1) for e in sample)

    generator = generators.Date(item, 'foo', after=date(2012, 10, 10))
    sample = take(generator, 100)
    assert all(e >= date(2012, 10, 10) for e in sample)
    assert all(e <= date.today() for e in sample)

    generator = generators.Date(item, 'foo', after=date(2012, 10, 10),
                                future=True)
    sample = take(generator, 100)
    assert all(e >= date(2012, 10, 10) for e in sample)
    assert all(e <= date(2100, 1, 1) for e in sample)

    generator = generators.Date(item, 'foo', before=date(2012, 10, 10))
    sample = take(generator, 100)
    assert all(e >= date(1900, 1, 1) for e in sample)
    assert all(e <= date(2012, 10, 10) for e in sample)

    generator = generators.Date(item, 'foo', before=date(2012, 10, 10),
                                future=True)
    sample = take(generator, 100)
    assert all(e >= date(1900, 1, 1) for e in sample)
    assert all(e <= date(2012, 10, 10) for e in sample)

    generator = generators.Date(item, 'foo', after='$stop')
    blueprint.vars['stop'] = date(2012, 10, 10)
    sample = take(generator, 100)
    assert all(e >= date(2012, 10, 10) for e in sample)
    assert all(e <= date(2100, 1, 1) for e in sample)

    generator = generators.Date(item, 'foo', before='$start')
    blueprint.vars['start'] = date(2012, 10, 10)
    sample = take(generator, 100)
    assert all(e >= date(1900, 1, 1) for e in sample)
    assert all(e <= date(2012, 10, 10) for e in sample)

    generator = generators.Date(item, 'foo', after=2015, before=2016)
    sample = take(generator, 100)
    assert all(e.year == 2015 for e in sample)
    months = set(e.month for e in sample)
    for month in range(1, 12):
        assert month in months


def test_name(item):
    import random

    generator = generators.Name(item, 'foo')
    sample = take(generator, 10)
    assert len(sample) == 10
    assert all(isinstance(e, unicode) for e in sample)
    assert all(' ' in e for e in sample)

    generator = generators.Name(item, 'foo', max_length=30)
    sample = take(generator, 10)
    assert len(sample) == 10
    assert all(len(e) <= 30 for e in sample)

    random.seed(42)
    generator = generators.Name(item, 'foo', gender='F')
    female_sample = take(generator, 10)
    random.seed(42)
    generator = generators.Name(item, 'foo', gender='M')
    male_sample = take(generator, 10)
    assert female_sample != male_sample


def test_first_name(item):
    import random

    generator = generators.FirstName(item, 'foo')
    sample = take(generator, 10)
    assert len(sample) == 10
    assert all(isinstance(e, unicode) for e in sample)

    generator = generators.FirstName(item, 'foo', max_length=30)
    sample = take(generator, 10)
    assert len(sample) == 10
    assert all(len(e) <= 30 for e in sample)

    random.seed(42)
    generator = generators.FirstName(item, 'foo', gender='F')
    female_sample = take(generator, 10)
    random.seed(42)
    generator = generators.FirstName(item, 'foo', gender='M')
    male_sample = take(generator, 10)
    assert female_sample != male_sample


def test_last_name(item):
    generator = generators.LastName(item, 'foo')
    sample = take(generator, 10)
    assert len(sample) == 10
    assert all(isinstance(e, unicode) for e in sample)

    generator = generators.LastName(item, 'foo', max_length=30)
    sample = take(generator, 10)
    assert len(sample) == 10
    assert all(len(e) <= 30 for e in sample)


def test_ip(item):
    generator = generators.IP(item, 'foo')
    sample = take(generator, 100)
    assert len(sample) == 100
    assert all(validate_ip(ip) for ip in sample)
    assert any(validate_ip(ip, family='IPv4') for ip in sample)
    assert any(validate_ip(ip, family='IPv6') for ip in sample)


def test_ipv4(item):
    generator = generators.IP(item, 'foo', ipv6=False)
    sample = take(generator, 10)
    assert len(sample) == 10
    assert all(validate_ip(ip, family='IPv4') for ip in sample)
    assert not any(validate_ip(ip, family='IPv6') for ip in sample)


def test_ipv6(item):
    generator = generators.IP(item, 'foo', ipv4=False)
    sample = take(generator, 10)
    assert len(sample) == 10
    assert all(validate_ip(ip, family='IPv6') for ip in sample)
    assert not any(validate_ip(ip, family='IPv4') for ip in sample)


def test_url(item):
    generator = generators.URL(item, 'foo')
    sample = take(generator, 10)
    assert len(sample) == 10
    assert all('.' in e for e in sample)
    assert all(e.startswith('http') for e in sample)
    assert all(not e.endswith('/') for e in sample)
