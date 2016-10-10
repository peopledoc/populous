from datetime import date

from populous.backends.base import Backend
from populous.blueprint import Blueprint
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

    mocker.patch.object(blueprint.items['foo'], 'generate')
    mocker.patch.object(blueprint.items['bar'], 'generate')
    mocker.patch.object(blueprint.items['lol'], 'generate')

    buffer = mocker.MagicMock()
    blueprint.generate(buffer)

    assert blueprint.items['foo'].generate.call_args == mocker.call(buffer, 10)
    assert blueprint.items['bar'].generate.called is False
    assert blueprint.items['lol'].generate.call_args == mocker.call(buffer, 17)
