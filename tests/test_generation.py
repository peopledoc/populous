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
