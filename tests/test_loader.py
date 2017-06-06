import pytest

from populous import loader
from populous.blueprint import Blueprint
from populous.exceptions import ValidationError
from populous.exceptions import YAMLError


def test_load_blueprint(mocker):
    files = {
        'test1.yaml': {'vars': {'foo': None}},
        'test2.yaml': {'vars': {'bar': 42}},
        'test3.yaml': {'vars': {'baz': 'lol', 'foo': 'bar'}},
    }
    mocker.patch('populous.loader._get_yaml',
                 wraps=lambda filename: files[filename])

    blueprint = loader.load_blueprint('test1.yaml', 'test2.yaml', 'test3.yaml')

    assert blueprint.vars['foo'] == 'bar'
    assert blueprint.vars['bar'] == 42
    assert blueprint.vars['baz'] == 'lol'


def test_load_blueprint_validation_error(mocker):
    mocker.patch('populous.loader._get_yaml')
    mocker.patch('populous.loader._load_content',
                 side_effect=ValidationError('foo'))

    with pytest.raises(ValidationError) as exc:
        loader.load_blueprint('foo.yml')

    e = exc.value
    assert e.filename == 'foo.yml'
    assert str(e) == "File 'foo.yml': foo"


def test_load_blueprint_yaml_error(mocker):
    mocker.patch('populous.loader._get_yaml',
                 side_effect=YAMLError('foo.yml', 'foo'))

    with pytest.raises(YAMLError) as exc:
        loader.load_blueprint('foo.yml')

    e = exc.value
    assert str(e) == "Error parsing 'foo.yml': foo"


def test_get_yaml(mocker):
    content = 'foo: bar'
    mocker.patch('populous.loader.open', mocker.mock_open(read_data=content))

    assert loader._get_yaml('foo.yml') == {'foo': 'bar'}


def test_get_yaml_error(mocker):
    file_mock = mocker.mock_open(read_data=':')
    file_mock.name = 'foo.yml'
    mocker.patch('populous.loader.open', file_mock)

    with pytest.raises(YAMLError) as exc:
        loader._get_yaml('foo.yml')

    e = exc.value
    assert str(e).startswith("Error parsing 'foo.yml': ")
    assert str(e).endswith('line 1, column 1')


def test_load_content(mocker):
    bp = Blueprint()
    load_vars = mocker.patch('populous.loader._load_vars')
    load_items = mocker.patch('populous.loader._load_items')

    # empty content
    loader._load_content(bp, None)
    loader._load_content(bp, {})
    loader._load_content(bp, [])
    assert load_vars.called is False
    assert load_items.called is False

    # wrong type
    with pytest.raises(ValidationError) as e:
        loader._load_content(bp, ['foo'])
    assert "Got a 'list'" in str(e.value)

    # unknown keys
    with pytest.raises(ValidationError) as e:
        loader._load_content(bp, {'foo': None})
    assert "Unknown key(s) in blueprint: 'foo'" in str(e.value)

    with pytest.raises(ValidationError) as e:
        loader._load_content(bp, {'items': None, 'foo': None, 'bar': None})
    assert "Unknown key(s) in blueprint: 'bar, foo'" in str(e.value)

    # valid content
    mocker.resetall()
    loader._load_content(bp, {'items': [{'foo': 42}]})
    assert load_vars.call_args == mocker.call(bp, {})
    assert load_items.call_args == mocker.call(bp, [{'foo': 42}])

    mocker.resetall()
    loader._load_content(bp, {'vars': {'foo': 'bar'}})
    assert load_vars.call_args == mocker.call(bp, {'foo': 'bar'})
    assert load_items.call_args == mocker.call(bp, [])

    mocker.resetall()
    loader._load_content(
        bp, {'vars': {'foo': 'bar'}, 'items': [{'bar': 'foo'}]}
    )
    assert load_vars.call_args == mocker.call(bp, {'foo': 'bar'})
    assert load_items.call_args == mocker.call(bp, [{'bar': 'foo'}])


def test_load_vars(mocker):
    bp = Blueprint()
    add_var = mocker.patch.object(bp, 'add_var')

    # wrong type
    with pytest.raises(ValidationError) as e:
        loader._load_vars(bp, ['foo'])
    assert "must be a dict, not a list." in str(e.value)

    # empty value
    loader._load_vars(bp, {})
    assert add_var.called is False

    # valid values
    loader._load_vars(bp, {'foo': 'bar', 'bar': None, 'baz': 42, 'lol': [42]})
    assert sorted(add_var.call_args_list) == [
        mocker.call('bar', None),
        mocker.call('baz', 42),
        mocker.call('foo', 'bar'),
        mocker.call('lol', [42]),
    ]


def test_load_items(mocker):
    bp = Blueprint()
    add_item = mocker.patch.object(bp, 'add_item')

    # wrong type
    with pytest.raises(ValidationError) as e:
        loader._load_items(bp, {'foo': 'bar'})
    assert "must be in a list, not a dict." in str(e.value)

    # empty value
    loader._load_items(bp, [])
    assert add_item.called is False

    # valid values
    loader._load_items(bp, [{'foo': 'bar'}, {'bar': 'lol'}])
    assert add_item.call_args_list == [
        mocker.call({'foo': 'bar'}),
        mocker.call({'bar': 'lol'}),
    ]
