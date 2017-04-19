import pytest

from populous import generators
from populous.blueprint import Blueprint
from populous.exceptions import ValidationError
from populous.vars import ValueExpression


def test_description_wrong_type():
    blueprint = Blueprint()

    msg = "A blueprint item must be a dict, not a 'NoneType'"
    with pytest.raises(ValidationError) as e:
        blueprint.add_item(None)
    assert msg in str(e.value)

    msg = "A blueprint item must be a dict, not a 'int'"
    with pytest.raises(ValidationError) as e:
        blueprint.add_item(42)
    assert msg in str(e.value)

    msg = "A blueprint item must be a dict, not a 'list'"
    with pytest.raises(ValidationError) as e:
        blueprint.add_item([])
    assert msg in str(e.value)


def test_name_and_table():
    blueprint = Blueprint()

    blueprint.add_item({'name': 'foo', 'table': 'bar'})
    item = blueprint.items['foo']
    assert item.name == 'foo'
    assert item.table == 'bar'
    assert item.fields.keys() == ['id']


def test_required():
    blueprint = Blueprint()

    msg = "Items without a parent must have a name"
    with pytest.raises(ValidationError) as e:
        blueprint.add_item({})
    assert msg in str(e.value)

    msg = "Item 'foo' does not have a table."
    with pytest.raises(ValidationError) as e:
        blueprint.add_item({'name': 'foo'})
    assert msg in str(e.value)


def test_with_extra_keys():
    blueprint = Blueprint()

    msg = ("Unknown key(s) 'foo'. Possible keys are 'name, parent, "
           "table, count, fields, store_in'.")
    with pytest.raises(ValidationError) as e:
        blueprint.add_item({'name': 'foo', 'table': 'bar', 'foo': 'bar'})
    assert msg in str(e.value)


def test_two_parents():
    blueprint = Blueprint()

    blueprint.add_item({'name': 'foo', 'table': 'bar'})

    msg = "Re-defining item 'foo' while setting 'bar' as parent is ambiguous"
    with pytest.raises(ValidationError) as e:
        blueprint.add_item({'name': 'foo', 'parent': 'bar'})
    assert msg in str(e.value)


def test_unexisting_parent():
    blueprint = Blueprint()

    msg = "Parent 'foo' does not exist."
    with pytest.raises(ValidationError) as e:
        blueprint.add_item({'name': 'test', 'parent': 'foo'})
    assert msg in str(e.value)


def test_set_parent():
    blueprint = Blueprint()

    blueprint.add_item({'name': 'foo', 'table': 'bar'})
    blueprint.add_item({'name': 'bar', 'parent': 'foo'})

    assert 'foo' in blueprint.items
    assert 'bar' in blueprint.items

    foo = blueprint.items['foo']
    bar = blueprint.items['bar']
    assert foo.name == 'foo'
    assert bar.name == 'bar'
    assert bar.table == 'bar'


def test_parent_with_same_name():
    blueprint = Blueprint()

    blueprint.add_item({'name': 'foo', 'table': 'bar'})
    blueprint.add_item({'name': 'foo', 'table': 'test'})

    assert len(blueprint.items) == 1
    assert blueprint.items['foo'].table == 'test'


def test_parent_without_name():
    blueprint = Blueprint()

    blueprint.add_item({'name': 'foo', 'table': 'bar'})
    blueprint.add_item({'parent': 'foo', 'table': 'test'})

    assert len(blueprint.items) == 1
    assert blueprint.items['foo'].table == 'test'


def test_store_in_not_dict():
    blueprint = Blueprint()

    msg = "'store_in' must be a dict, not a 'int'"
    with pytest.raises(ValidationError) as e:
        blueprint.add_item({'name': 'foo', 'store_in': 42})
    assert msg in str(e.value)


def test_store_in():
    blueprint = Blueprint()

    blueprint.add_item({'name': 'toto', 'table': 'toto'})
    blueprint.add_item({'name': 'foo', 'table': 'bar',
                        'count': {'by': 'toto'},
                        'store_in': {
                            'foo': '$bar',
                            'test': 'foo',
                            'this.toto.foos': '$this.id'
                        }})

    toto = blueprint.items['toto']
    foo = blueprint.items['foo']

    assert isinstance(foo.store_in_global['foo'], ValueExpression)
    assert foo.store_in_global['foo'].var == 'bar'
    assert foo.store_in_global['test'] == 'foo'

    assert len(foo.store_in_item) == 1
    name_expr = foo.store_in_item.keys()[0]
    assert name_expr.var == 'this'
    assert name_expr.attrs == 'toto.foos'
    value_expr = foo.store_in_item.values()[0]
    assert value_expr.var == 'this'
    assert value_expr.attrs == 'id'

    assert 'foo' in blueprint.vars
    assert 'test' in blueprint.vars

    assert 'foos' in toto.fields
    assert next(toto.fields['foos']) == []
    assert id(next(toto.fields['foos'])) != id(next(toto.fields['foos']))


def test_store_in_non_existing_item():
    blueprint = Blueprint()

    msg = ("Error in 'store_in' section in item 'foo': The "
           "item 'toto' does not exist.")
    with pytest.raises(ValidationError) as e:
        blueprint.add_item({'name': 'foo', 'table': 'bar',
                            'count': {'by': 'toto'},
                            'store_in': {
                                'this.toto.foos': '$this.id'
                            }})
    assert msg in str(e.value)


def test_inherit_store_in():
    blueprint = Blueprint()

    blueprint.add_item({'name': 'foo', 'table': 'bar',
                        'store_in': {'foo': 'bar'}})
    blueprint.add_item({'name': 'bar', 'parent': 'foo'})
    assert blueprint.items['bar'].store_in_global == {'foo': 'bar'}

    blueprint.add_item({'name': 'lol', 'parent': 'foo',
                        'store_in': {'test': 'foo'}})
    assert blueprint.items['lol'].store_in_global == {'test': 'foo'}


def test_fields_not_dict():
    blueprint = Blueprint()

    msg = "Fields must be a dict, not a 'int'"
    with pytest.raises(ValidationError) as e:
        blueprint.add_item({'name': 'foo', 'table': 'bar', 'fields': 42})
    assert msg in str(e.value)


def test_field_value():
    blueprint = Blueprint()

    blueprint.add_item({'name': 'foo', 'table': 'bar',
                        'fields': {'a': None, 'b': 42, 'c': '$foo', 'd': ''}})
    item = blueprint.items['foo']

    assert isinstance(item.fields['a'], generators.Value)
    assert item.fields['a'].value is None

    assert isinstance(item.fields['b'], generators.Value)
    assert item.fields['b'].value == 42

    assert isinstance(item.fields['c'], generators.Value)
    assert isinstance(item.fields['c'].value, ValueExpression)
    assert item.fields['c'].value.var == 'foo'

    assert isinstance(item.fields['d'], generators.Value)
    assert item.fields['d'].value == ''


def test_field_without_generator():
    blueprint = Blueprint()

    msg = ("Field 'a' in item 'foo' must either be a value, or "
           "a dict with a 'generator' key.")
    with pytest.raises(ValidationError) as e:
        blueprint.add_item({'name': 'foo', 'table': 'bar',
                            'fields': {'a': {'foo': 'bar'}}})
    assert msg in str(e.value)


def test_field_with_generator():
    blueprint = Blueprint()

    blueprint.add_item({'name': 'foo', 'table': 'bar',
                        'fields': {'a': {'generator': 'Integer', 'max': 42}}})
    item = blueprint.items['foo']

    assert isinstance(item.fields['a'], generators.Integer)
    assert item.fields['a'].max == 42


def test_field_extra_params():
    blueprint = Blueprint()

    msg = ("Item 'foo', field 'a': Got extra param(s) for generator "
           "'Integer': foo")
    with pytest.raises(ValidationError) as e:
        blueprint.add_item({'name': 'foo', 'table': 'bar',
                            'fields': {
                                'a': {'generator': 'Integer', 'foo': 42}
                            }})
    assert msg in str(e.value)


def test_field_non_existing_generator():
    blueprint = Blueprint()

    msg = "Item 'foo', field 'a': Generator 'Foo' does not exist."
    with pytest.raises(ValidationError) as e:
        blueprint.add_item({'name': 'foo', 'table': 'bar',
                           'fields': {'a': {'generator': 'Foo'}}})
    assert msg in str(e.value)


def test_field_inheritance():
    blueprint = Blueprint()

    blueprint.add_item({
        'name': 'foo',
        'table': 'bar',
        'fields': {
            'a': {'generator': 'Integer', 'min': 10, 'max': 20}
        }
    })
    blueprint.add_item({
        'name': 'test1',
        'parent': 'foo',
        'fields': {
            'b': {'generator': 'Value', 'value': 'foo'}
        }
    })

    foo = blueprint.items['foo']

    # if we inherit from an item, we get a copy of its fields
    test1 = blueprint.items['test1']
    assert isinstance(test1.fields['a'], generators.Integer)
    assert test1.fields['a'].min == 10
    assert test1.fields['a'].max == 20
    assert test1.fields['a'] != foo.fields['a']
    assert isinstance(test1.fields['b'], generators.Value)
    assert test1.fields['b'].value == 'foo'

    # if we change the generator, the attributes should not be copied
    blueprint.add_item({
        'name': 'test2',
        'parent': 'foo',
        'fields': {
            'a': {'generator': 'Value', 'value': 'foo'}
        }
    })
    test2 = blueprint.items['test2']
    assert isinstance(test2.fields['a'], generators.Value)
    assert test2.fields['a'].value == 'foo'
    assert not hasattr(test2.fields['a'], 'min')

    # if we don't change the generator, the attributes are copied and
    # can be overriden
    blueprint.add_item({
        'name': 'test3',
        'parent': 'foo',
        'fields': {
            'a': {'max': 42}
        }
    })
    test3 = blueprint.items['test3']
    assert isinstance(test3.fields['a'], generators.Integer)
    assert test3.fields['a'].min == 10
    assert test3.fields['a'].max == 42
    assert test3.fields['a'] != foo.fields['a']


def test_without_count():
    blueprint = Blueprint()

    blueprint.add_item({'name': 'foo', 'table': 'bar'})
    assert blueprint.items['foo'].count.number == 0
    assert blueprint.items['foo'].count() == 0


def test_count_valid():
    blueprint = Blueprint()

    blueprint.add_item({'name': 'test1', 'table': 'bar', 'count': 42})
    assert blueprint.items['test1'].count.number == 42
    assert blueprint.items['test1'].count() == 42

    blueprint.add_item({'name': 'test2', 'table': 'bar',
                        'count': {'min': 10, 'max': 100}})
    assert blueprint.items['test2'].count.number is None
    assert blueprint.items['test2'].count.min == 10
    assert blueprint.items['test2'].count.max == 100
    assert 10 <= blueprint.items['test2'].count() <= 100

    blueprint.add_item({'name': 'foo', 'table': 'bar'})
    blueprint.add_item({'name': 'test3', 'table': 'bar',
                        'count': {'number': 42, 'by': 'foo'}})
    assert blueprint.items['test3'].count.number == 42
    assert blueprint.items['test3'].count.by == 'foo'


def test_count_var():
    blueprint = Blueprint()

    blueprint.add_item({'name': 'test1', 'table': 'bar', 'count': '$foo'})
    blueprint.vars['foo'] = 42
    assert blueprint.items['test1'].count() == 42

    blueprint.add_item({'name': 'test2', 'table': 'bar',
                        'count': {'min': '$min', 'max': '$max'}})
    blueprint.vars['min'] = 1
    blueprint.vars['max'] = 10
    assert 1 <= blueprint.items['test2'].count() <= 10


def test_count_invalid():
    blueprint = Blueprint()

    msg = "The count of item 'foo' must be an integer or a dict"
    with pytest.raises(ValidationError) as e:
        blueprint.add_item({'name': 'foo', 'table': 'bar', 'count': '42'})
    assert msg in str(e.value)

    msg = ("Unknown key(s) 'test' in count of item 'foo'. Possible keys "
           "are 'number, by, min, max'.")
    with pytest.raises(ValidationError) as e:
        blueprint.add_item({'name': 'foo', 'table': 'bar',
                            'count': {'test': 'bar'}})
    assert msg in str(e.value)

    msg = ("Item 'foo' count: number must be an integer or a variable (got: "
           "'str').")
    with pytest.raises(ValidationError) as e:
        blueprint.add_item({'name': 'foo', 'table': 'bar',
                            'count': {'number': '42'}})
    assert msg in str(e.value)

    msg = "Item 'foo' count: min must be positive."
    with pytest.raises(ValidationError) as e:
        blueprint.add_item({'name': 'foo', 'table': 'bar',
                            'count': {'min': -42}})
    assert msg in str(e.value)

    msg = "Item 'foo' count: Min is greater than max."
    with pytest.raises(ValidationError) as e:
        blueprint.add_item({'name': 'foo', 'table': 'bar',
                            'count': {'min': 42, 'max': 10}})
    assert msg in str(e.value)


def test_count_inheritance():
    blueprint = Blueprint()

    blueprint.add_item({'name': 'foo', 'table': 'bar', 'count': 42})
    blueprint.add_item({'name': 'bar', 'table': 'bar',
                        'count': {'min': 10, 'max': 100, 'by': 'foo'}})

    # if not specified the count should be inherited
    blueprint.add_item({'name': 'test1', 'parent': 'foo'})
    assert blueprint.items['test1'].count.number == 42

    # we can change it
    blueprint.add_item({'name': 'test2', 'parent': 'foo', 'count': 10})
    assert blueprint.items['test2'].count.number == 10

    # we also inherit from min, max and by
    blueprint.add_item({'name': 'test3', 'parent': 'bar'})
    assert blueprint.items['test3'].count.min == 10
    assert blueprint.items['test3'].count.max == 100
    assert blueprint.items['test3'].count.by == 'foo'

    # if we set number and our parent min/max, we don't inherit them
    blueprint.add_item({'name': 'test4', 'parent': 'bar',
                        'count': {'number': 42}})
    assert blueprint.items['test4'].count.min == 0
    assert blueprint.items['test4'].count.max == 0
    assert blueprint.items['test4'].count.by == 'foo'
    assert blueprint.items['test4'].count.number == 42

    # we can change by and min/max
    blueprint.add_item({'name': 'test5', 'parent': 'bar',
                        'count': {'by': 'bar', 'min': 20}})
    assert blueprint.items['test5'].count.min == 20
    assert blueprint.items['test5'].count.max == 100
    assert blueprint.items['test5'].count.by == 'bar'

    # we can change only min/max
    blueprint.add_item({'name': 'test6', 'parent': 'bar',
                        'count': {'max': 20}})
    assert blueprint.items['test6'].count.min == 10
    assert blueprint.items['test6'].count.max == 20
    assert blueprint.items['test6'].count.by == 'foo'

    # we can set min and max to 0
    blueprint.add_item({'name': 'test7', 'parent': 'bar',
                        'count': {'min': 0, 'max': 0}})
    assert blueprint.items['test7'].count.min == 0
    assert blueprint.items['test7'].count.max == 0
    assert blueprint.items['test7'].count.by == 'foo'


def test_add_var():
    blueprint = Blueprint()

    blueprint.add_var('foo', 42)
    blueprint.add_var('bar', None)

    assert blueprint.vars['foo'] == 42
    assert blueprint.vars['bar'] is None
