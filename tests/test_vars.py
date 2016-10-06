import pytest

from populous.vars import parse_vars
from populous.exceptions import GenerationError


def test_parse_vars(mocker):
    class Expression(object):
        def __init__(self, value):
            self.value = value

        def __eq__(self, other):
            return type(self) == type(other) and self.value == other.value

        def __repr__(self):
            return "{}('{}')".format(type(self).__name__, self.value)

    class Value(Expression):
        pass

    class Template(Expression):
        pass

    assert Value('foo') != Template('foo')
    assert Value('foo') != Value('bar')

    mocker.patch('populous.vars.ValueExpression', wraps=Value)
    mocker.patch('populous.vars.TemplateExpression', wraps=Template)

    assert parse_vars(None) is None
    assert parse_vars(0) == 0
    assert parse_vars('') == ''
    assert parse_vars('foo') == 'foo'

    assert parse_vars('$foo') == Value('foo')
    assert parse_vars('$foo.bar') == Value('foo.bar')
    assert parse_vars('$foo.bar.lol') == Value('foo.bar.lol')
    assert parse_vars('$_a2.x3_') == Value('_a2.x3_')

    assert parse_vars(r'\$foo') == '$foo'
    assert parse_vars(r'\$foo.bar') == '$foo.bar'

    assert parse_vars('$foo bar') == Template('$foo bar')
    assert parse_vars('foo $bar') == Template('foo $bar')
    assert parse_vars('{foo} $bar') == Template('{foo} $bar')
    assert parse_vars('$foo$bar') == Template('$foo$bar')
    assert parse_vars('$foo.bar$lol') == Template('$foo.bar$lol')
    assert parse_vars(r'\$$foo') == Template(r'\$$foo')
    assert parse_vars('$$foo') == Template('$$foo')


def test_value_expression():
    from populous.vars import ValueExpression

    v = ValueExpression('foo')
    assert v.evaluate(foo='bar') == 'bar'
    assert v.evaluate(foo=1) == 1
    assert v.evaluate(foo=None) is None
    assert v.evaluate(foo=[1, 2, 3]) == [1, 2, 3]

    with pytest.raises(GenerationError) as e:
        v.evaluate()
    assert "Variable 'foo' not found." in str(e.value)

    class Val(object):
        None

    a = Val()
    a.b = 'foo'
    a.c = Val()
    a.c.d = 42
    assert ValueExpression('a.b').evaluate(a=a) == 'foo'
    assert ValueExpression('a.c.d').evaluate(a=a) == 42

    with pytest.raises(GenerationError) as e:
        ValueExpression('a.b').evaluate(a=42)
    assert "'int' object has no attribute 'b'" in str(e.value)


def test_template_expression():
    from populous.vars import TemplateExpression

    t = TemplateExpression('$foo bar')
    assert t.evaluate(foo='test') == 'test bar'
    assert t.evaluate(foo='$foo') == '$foo bar'
    assert t.evaluate(foo=42) == '42 bar'
    assert t.evaluate(foo=None) == 'None bar'
    assert t.evaluate(foo='') == ' bar'

    t = TemplateExpression('$foo $foo $foo')
    assert t.evaluate(foo='test') == 'test test test'

    t = TemplateExpression(r"\$foo $bar \$\$lol")
    assert t.evaluate(bar='test') == '$foo test $$lol'

    t = TemplateExpression('{$foo}')
    assert t.evaluate(foo='test') == '{test}'

    t = TemplateExpression('$foo$bar')
    assert t.evaluate(foo='test', bar=42) == 'test42'

    t = TemplateExpression('$foo:s')
    assert t.evaluate(foo='test') == 'test:s'

    class Val(object):
        None

    a = Val()
    a.b = 'foo'
    a.c = Val()
    a.c.d = 42
    t = TemplateExpression('$var.b - $var.c.d')
    assert t.evaluate(var=a) == 'foo - 42'

    t = TemplateExpression('$foo $bar $lol')
    with pytest.raises(GenerationError) as e:
        t.evaluate(foo='test')
    assert "Variable 'bar' not found." in str(e.value)

    t = TemplateExpression('$foo.bar')
    with pytest.raises(GenerationError) as e:
        t.evaluate(foo=42)
    assert "'int' object has no attribute 'bar'" in str(e.value)
