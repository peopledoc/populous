from datetime import date

from populous.backends.base import Backend
from populous.blueprint import Blueprint
from populous.buffer import Buffer
from populous.factory import ItemFactory
from populous.item import Item


def test_blueprint_preprocess(mocker):
    blueprint = Blueprint()

    blueprint.add_item({'name': 'foo', 'table': 'test'})
    blueprint.add_item({'name': 'bar', 'table': 'test'})

    foo = mocker.Mock(wraps=blueprint.items['foo'])
    bar = mocker.Mock(wraps=blueprint.items['bar'])
    blueprint.items['foo'] = foo
    blueprint.items['bar'] = bar

    blueprint.preprocess()
    assert foo.preprocess.called is True
    assert bar.preprocess.called is True


def test_item_preprocess(mocker):
    existing = (
        (1, 'Homer', 'Simpson', date(1956, 6, 18), 'M'),
        (2, 'Marge', 'Simpson', date(1959, 6, 29), 'F'),
        (3, 'Bart', 'Simpson', date(1981, 4, 1), 'M'),
        (4, 'Lisa', 'Simpson', date(1984, 5, 9), 'F'),
        (5, 'Maggie', 'Simpson', date(1988, 11, 7), 'F')
    )

    class DummyBackend(Backend):
        def select(self, *args, **kwargs):
            return iter(existing)

    blueprint = Blueprint(backend=mocker.Mock(wraps=DummyBackend()))
    item = Item(blueprint, 'person', 'test')

    item.add_field('id', 'Integer', unique=True)
    item.add_field('firstname', 'Text', unique=['lastname', 'birth'])
    item.add_field('lastname', 'Text')
    item.add_field('birth', 'Date')
    item.add_field('gender', 'Choices', choices=['M', 'F'])

    item.preprocess()
    assert blueprint.backend.select.call_args == mocker.call(
        'test', ['id', 'firstname', 'lastname', 'birth'])

    assert 1 in item.fields['id'].seen
    assert 5 in item.fields['id'].seen
    assert 6 not in item.fields['id'].seen

    seen = item.fields['firstname'].seen
    assert ('Homer', 'Simpson', date(1956, 6, 18)) in seen
    assert ('Lisa', 'Simpson', date(1984, 5, 9)) in seen
    assert ('Bart', 'Simpson', date(2016, 10, 9)) not in seen


def test_blueprint_generate(mocker):
    import random
    random.seed(42)

    blueprint = Blueprint()

    blueprint.add_item({'name': 'foo', 'table': 'test', 'count': 10})
    blueprint.add_item({'name': 'bar', 'table': 'test',
                        'count': {'number': 20, 'by': 'foo'}})
    blueprint.add_item({'name': 'lol', 'table': 'test',
                        'count': {'min': 10, 'max': 20}})
    foo = blueprint.items['foo']
    bar = blueprint.items['bar']
    lol = blueprint.items['lol']

    mocker.patch.object(foo, 'generate')
    mocker.patch.object(bar, 'generate')
    mocker.patch.object(lol, 'generate')

    buffer = mocker.Mock(wraps=Buffer(blueprint))
    mocker.patch('populous.blueprint.Buffer', return_value=buffer)

    blueprint.generate()

    assert foo.generate.call_args == mocker.call(buffer, 10)
    assert bar.generate.called is False
    assert lol.generate.call_args == mocker.call(buffer, 17)

    assert buffer.flush.called is True


def test_item_generate():
    blueprint = Blueprint()

    blueprint.add_item({'name': 'foo', 'table': 'test',
                        'fields': {
                            'a': {'generator': 'Text'},
                            'b': {'generator': 'Integer'}
                        }})
    item = blueprint.items['foo']

    buffer = Buffer(blueprint)
    item.generate(buffer, 10)

    assert list(buffer.buffers.keys()) == ['foo']
    assert len(buffer.buffers['foo']) == 10

    for obj in buffer.buffers['foo']:
        assert isinstance(obj.a, str)
        assert isinstance(obj.b, int)


def test_item_generate_this_var(mocker):
    blueprint = Blueprint()
    blueprint.add_item({'name': 'foo', 'table': 'test'})
    item = blueprint.items['foo']

    call_count = {'count': 0}

    def _generate(self):
        call_count['count'] += 1
        assert self.blueprint.vars['this'] == self

    mocker.patch.object(ItemFactory, 'generate', _generate)
    buffer = Buffer(blueprint)
    item.generate(buffer, 10)

    assert call_count['count'] == 10


def test_write_buffer(mocker):
    class DummyBackend(Backend):
        def write(self, item, objs):
            return range(len(objs))

    blueprint = Blueprint(backend=DummyBackend())
    blueprint.add_item({'name': 'foo', 'table': 'test', 'fields': {'a': 42}})
    item = blueprint.items['foo']

    mocker.patch.object(item, 'store_values')
    mocker.patch.object(item, 'generate_dependencies')

    buffer = Buffer(blueprint, maxlen=10)
    item.generate(buffer, 10)

    objs = tuple(item.namedtuple(id=x, a=42) for x in xrange(10))
    assert len(buffer.buffers['foo']) == 0
    assert item.store_values.call_args == mocker.call(objs)
    assert item.generate_dependencies.call_args == mocker.call(buffer, objs)


def test_flush_buffer(mocker):
    blueprint = Blueprint(backend=mocker.MagicMock())
    blueprint.add_item({'name': 'foo', 'table': 'test'})
    blueprint.add_item({'name': 'bar', 'table': 'test'})

    buffer = Buffer(blueprint)
    blueprint.items['foo'].generate(buffer, 5)
    blueprint.items['bar'].generate(buffer, 4)
    assert len(buffer.buffers['foo']) == 5
    assert len(buffer.buffers['bar']) == 4

    buffer.flush()
    assert len(buffer.buffers['foo']) == 0
    assert len(buffer.buffers['bar']) == 0

    assert blueprint.backend.write.call_count == 2
    assert (
        blueprint.backend.write.call_args_list[0] ==
        mocker.call(blueprint.items['foo'], ((), (), (), (), ()))
    )
    assert (
        blueprint.backend.write.call_args_list[1] ==
        mocker.call(blueprint.items['bar'], ((), (), (), ()))
    )


def test_generate_dependencies():
    class DummyBackend(Backend):
        def write(self, item, objs):
            return range(len(objs))

    blueprint = Blueprint(backend=DummyBackend())
    blueprint.add_item({'name': 'foo', 'table': 'test'})
    blueprint.add_item({'name': 'bar', 'table': 'test',
                        'count': {'number': 2, 'by': 'foo'},
                        'fields': {'parent_id': '$this.foo.id'}})
    blueprint.add_item({'name': 'lol', 'table': 'test',
                        'count': {'min': 1, 'max': 2, 'by': 'foo'},
                        'fields': {'parent_id': '$this.foo.id'}})
    blueprint.add_item({'name': 'abc', 'table': 'test'})
    blueprint.add_item({'name': 'baz', 'table': 'test',
                        'count': {'number': 20, 'by': 'abc'}})

    buffer = Buffer(blueprint)
    blueprint.items['foo'].generate(buffer, 10)
    assert list(buffer.buffers.keys()) == ['foo']

    buffer.write('foo', buffer.buffers['foo'])
    assert list(buffer.buffers.keys()) == ['foo', 'bar', 'lol']
    assert len(buffer.buffers['foo']) == 0
    assert len(buffer.buffers['bar']) == 20
    assert 10 <= len(buffer.buffers['lol']) <= 20

    def ids():
        for x in xrange(10):
            yield x
            yield x

    for x, bar in zip(ids(), buffer.buffers['bar']):
        assert bar.parent_id == x
        assert bar.foo.id == x


def test_store_values():
    class DummyBackend(Backend):
        def write(self, item, objs):
            return range(len(objs))

    blueprint = Blueprint(backend=DummyBackend())
    blueprint.add_item({'name': 'foo', 'table': 'test',
                        'store_in': {'ids': '$this.id'}})
    item = blueprint.items['foo']

    buffer = Buffer(blueprint)
    item.generate(buffer, 10)
    buffer.flush()

    assert list(blueprint.vars['ids']) == list(range(10))
