from datetime import date

from populous.backends.base import Backend
from populous.blueprint import Blueprint
from populous.buffer import Buffer
from populous.compat import PY2
from populous.compat import range
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
    columns = ('id', 'firstname', 'lastname', 'birth', 'gender')
    existing = (
        (1, 'Homer', 'Simpson', date(1956, 6, 18), 'M'),
        (2, 'Marge', 'Simpson', date(1959, 6, 29), 'F'),
        (3, 'Bart', 'Simpson', date(1981, 4, 1), 'M'),
        (4, 'Lisa', 'Simpson', date(1984, 5, 9), 'F'),
        (5, 'Maggie', 'Simpson', date(1988, 11, 7), 'F')
    )

    class DummyBackend(Backend):
        def select(self, table, fields, **kwargs):
            for row in existing:
                yield tuple(row[columns.index(field)] for field in fields)

    blueprint = Blueprint(backend=mocker.Mock(wraps=DummyBackend()))
    item = Item(blueprint, 'person', 'test')

    item.add_field('id', 'Integer', unique=True)
    item.add_field('firstname', 'Text', unique=['lastname', 'birth'])
    item.add_field('lastname', 'Text')
    item.add_field('birth', 'Date')
    item.add_field('gender', 'Choices', choices=['M', 'F'])
    # add a unique field, but which isn't present in the db (shadow)
    item.add_field('parent', 'Choices', shadow=True, choices='$parents',
                   unique=['birth'])

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

    # add an item using the same table
    item2 = Item(blueprint, 'person2', 'test')
    item2.add_field('firstname', 'Text', unique=['lastname', 'birth'])
    item2.add_field('lastname', 'Text')
    # for this item, the date is unique
    item2.add_field('birth', 'Date', unique=True)

    blueprint.backend.select.reset_mock()
    item2.preprocess()
    # we should have queried only the birth
    assert blueprint.backend.select.call_args == mocker.call('test', ['birth'])

    seen = item2.fields['birth'].seen
    assert date(1956, 6, 18) in seen

    # we should use the same filter than for person
    seen = item2.fields['firstname'].seen
    assert ('Homer', 'Simpson', date(1956, 6, 18)) in seen


def test_item_preprocess_two_tables(mocker):
    class DummyBackend(Backend):
        def select(self, table, *args, **kwargs):
            if table == 'test1':
                return ['a', 'b', 'c']
            else:
                return ['1', '2', '3']

    blueprint = Blueprint(backend=mocker.Mock(wraps=DummyBackend()))

    foo = Item(blueprint, 'foo', 'test1')
    foo.add_field('code', 'Text', unique=True)

    bar = Item(blueprint, 'bar', 'test2')
    bar.add_field('code', 'Text', unique=True)

    bar2 = Item(blueprint, 'bar', 'test2')
    bar2.add_field('code', 'Text', unique=True)

    foo.preprocess()
    assert blueprint.backend.select.call_args == mocker.call('test1', ['code'])
    assert 'a' in foo.fields['code'].seen
    assert '1' not in foo.fields['code'].seen

    # same field name, but different table
    blueprint.backend.select.reset_mock()
    bar.preprocess()
    assert blueprint.backend.select.call_args == mocker.call('test2', ['code'])
    assert 'a' not in bar.fields['code'].seen
    assert '1' in bar.fields['code'].seen

    # same field name and table
    blueprint.backend.select.reset_mock()
    bar2.preprocess()
    assert blueprint.backend.select.call_args is None
    assert bar2.fields['code'].seen == bar.fields['code'].seen


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

    if PY2:
        assert lol.generate.call_args == mocker.call(buffer, 17)
    else:
        assert lol.generate.call_args == mocker.call(buffer, 20)
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
        return item.namedtuple(id=1)

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

    objs = tuple(item.namedtuple(id=x, a=42) for x in range(10))
    assert len(buffer.buffers['foo']) == 0
    assert item.store_values.call_args == mocker.call(objs)
    assert item.generate_dependencies.call_args == mocker.call(buffer, objs)


def test_write_empty_buffer(mocker):
    blueprint = Blueprint(backend=Backend())
    blueprint.add_item({'name': 'foo', 'table': 'test', 'fields': {'a': 42}})
    item = blueprint.items['foo']

    mocker.patch.object(blueprint.backend, 'write')

    buffer = Buffer(blueprint)
    # the buffer for the item is empty
    buffer.write(item)
    assert not blueprint.backend.write.called


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


def test_flush_buffer_with_dependencies(mocker):
    class DummyBackend(Backend):
        def write(self, item, objs):
            return range(len(objs))

    blueprint = Blueprint(backend=mocker.Mock(wraps=DummyBackend()))
    blueprint.add_item({'name': 'foo', 'table': 'test'})
    blueprint.add_item({'name': 'bar', 'table': 'test',
                        'count': {'number': 1, 'by': 'foo'}})

    blueprint.add_item({'name': 'lol', 'table': 'test',
                        'count': {'number': 1, 'by': 'bar'}})

    buffer = Buffer(blueprint)
    blueprint.items['foo'].generate(buffer, 5)
    assert len(buffer.buffers['foo']) == 5
    assert len(buffer.buffers['bar']) == 0
    assert len(buffer.buffers['lol']) == 0

    buffer.flush()
    assert len(buffer.buffers['foo']) == 0
    assert len(buffer.buffers['bar']) == 0
    assert len(buffer.buffers['lol']) == 0

    assert blueprint.backend.write.call_count == 3
    assert (
        blueprint.backend.write.call_args_list[0] ==
        mocker.call(blueprint.items['foo'], ((), (), (), (), ()))
    )
    assert (
        blueprint.backend.write.call_args_list[1] ==
        mocker.call(blueprint.items['bar'], ((), (), (), (), ()))
    )
    assert (
        blueprint.backend.write.call_args_list[2] ==
        mocker.call(blueprint.items['lol'], ((), (), (), (), ()))
    )


def test_generate_dependencies():
    class DummyBackend(Backend):
        def write(self, item, objs):
            return range(len(objs))

    blueprint = Blueprint(backend=DummyBackend())
    blueprint.add_item({'name': 'foo', 'table': 'test'})
    blueprint.add_item({'name': 'bar', 'table': 'test',
                        'count': {'number': 2, 'by': 'foo'},
                        'store_in': {'bars': '$this'},
                        'fields': {'parent_id': '$this.foo.id'}})
    blueprint.add_item({'name': 'lol', 'table': 'test',
                        'count': {'min': 1, 'max': 2, 'by': 'foo'},
                        'store_in': {'lols': '$this'},
                        'fields': {'parent_id': '$this.foo.id'}})
    blueprint.add_item({'name': 'abc', 'table': 'test'})
    blueprint.add_item({'name': 'baz', 'table': 'test',
                        'count': {'number': 20, 'by': 'abc'}})

    buffer = Buffer(blueprint)
    foo = blueprint.items['foo']
    foo.generate(buffer, 10)
    assert len(buffer.buffers['foo']) == 10
    assert len(buffer.buffers['bar']) == 0
    assert len(buffer.buffers['lol']) == 0

    buffer.write(foo)
    assert len(buffer.buffers['foo']) == 0
    assert len(buffer.buffers['bar']) == 0
    assert len(buffer.buffers['lol']) == 0

    assert len(blueprint.vars['bars']) == 20
    assert 10 <= len(blueprint.vars['lols']) <= 20

    def ids():
        for x in range(10):
            yield x
            yield x

    for x, bar in zip(ids(), blueprint.vars['bars']):
        assert bar.parent_id == x
        assert bar.foo.id == x


def test_generate_dependencies_ancestors():
    class DummyBackend(Backend):
        def write(self, item, objs):
            return range(len(objs))

    blueprint = Blueprint(backend=DummyBackend())
    blueprint.add_item({'name': 'foo', 'table': 'test'})
    blueprint.add_item({'name': 'foo2', 'parent': 'foo'})
    blueprint.add_item({'name': 'foo3', 'parent': 'foo2'})
    blueprint.add_item({'name': 'bar', 'table': 'test',
                        'count': {'number': 2, 'by': 'foo'},
                        'store_in': {'bars': '$this'},
                        'fields': {'parent_id': '$this.foo.id'}})

    buffer = Buffer(blueprint)
    foo2 = blueprint.items['foo2']
    foo3 = blueprint.items['foo3']
    foo3.generate(buffer, 2)
    foo2.generate(buffer, 2)
    assert len(buffer.buffers['foo2']) == 2
    assert len(buffer.buffers['foo3']) == 2
    assert len(buffer.buffers['bar']) == 0
    assert len(blueprint.vars['bars']) == 0

    buffer.write(foo3)
    assert len(buffer.buffers['foo2']) == 2
    assert len(buffer.buffers['foo3']) == 0
    assert len(buffer.buffers['bar']) == 0
    assert len(blueprint.vars['bars']) == 4

    buffer.write(foo2)
    assert len(buffer.buffers['foo2']) == 0
    assert len(buffer.buffers['foo3']) == 0
    assert len(buffer.buffers['bar']) == 0
    assert len(blueprint.vars['bars']) == 8


def test_generate_dependencies_tree():
    class DummyBackend(Backend):
        def write(self, item, objs):
            return range(len(objs))

    blueprint = Blueprint(backend=DummyBackend())

    # definition without count
    blueprint.add_item({'name': 'foo', 'table': 'test'})
    # root
    blueprint.add_item({'name': 'foo1', 'parent': 'foo',
                        'store_in': {'foo1s': '$this'},
                        'count': {'number': 2}})
    # level 2
    blueprint.add_item({'name': 'foo2', 'parent': 'foo1',
                        'store_in': {'foo2s': '$this'},
                        'count': {'number': 2, 'by': 'foo1'}})
    # level 3
    blueprint.add_item({'name': 'foo3', 'parent': 'foo2',
                        'store_in': {'foo3s': '$this'},
                        'count': {'number': 2, 'by': 'foo2'}})
    # item created for each foo (root or level)
    blueprint.add_item({'name': 'bar', 'table': 'test',
                        'store_in': {'bars': '$this'},
                        'count': {'number': 1, 'by': 'foo'}})

    buffer = Buffer(blueprint)
    foo1 = blueprint.items['foo1']
    foo1.generate(buffer, foo1.count())

    assert len(blueprint.vars['foo1s']) == 0
    assert len(blueprint.vars['foo2s']) == 0
    assert len(blueprint.vars['foo3s']) == 0
    assert len(blueprint.vars['bars']) == 0

    buffer.write(foo1)

    assert len(blueprint.vars['foo1s']) == 2
    assert len(blueprint.vars['foo2s']) == 4
    assert len(blueprint.vars['foo3s']) == 8
    assert len(blueprint.vars['bars']) == 14


def test_generate__count_with_var():
    class DummyBackend(Backend):
        def write(self, item, objs):
            return range(len(objs))

    blueprint = Blueprint(backend=DummyBackend())
    blueprint.add_item({'name': 'foo', 'table': 'test',
                        'fields': {'nb_bars': {
                            'generator': 'Integer', 'min': 1, 'max': 10
                        }},
                        'store_in': {'foos': '$this'}})
    blueprint.add_item({'name': 'bar', 'table': 'test',
                        'count': {'number': '$foo.nb_bars', 'by': 'foo'},
                        'store_in': {'this.foo.bars': '$this'}})

    buffer = Buffer(blueprint)
    blueprint.items['foo'].generate(buffer, 10)
    buffer.flush()

    assert len(blueprint.vars['foos']) == 10
    for foo in blueprint.vars['foos']:
        assert 1 <= foo.nb_bars <= 10
        assert len(foo.bars) == foo.nb_bars


def test_store_values():
    class DummyBackend(Backend):
        def write(self, item, objs):
            return range(len(objs))

    blueprint = Blueprint(backend=DummyBackend())
    blueprint.add_item({'name': 'foo', 'table': 'test',
                        'store_in': {'foos': '$this'}})
    blueprint.add_item({'name': 'bar', 'table': 'test2',
                        'count': {'by': 'foo', 'number': 2},
                        'store_in': {'this.foo.bar_ids': '$this.id'}})

    buffer = Buffer(blueprint)
    blueprint.items['foo'].generate(buffer, 10)
    buffer.flush()

    assert list(foo.id for foo in blueprint.vars['foos']) == list(range(10))

    ids = iter(range(20))
    for foo in blueprint.vars['foos']:
        assert foo.bar_ids == [next(ids), next(ids)]
