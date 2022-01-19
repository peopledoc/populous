import pytest

from populous.exceptions import GenerationError
from populous.exceptions import ValidationError
from populous.vars import parse_vars


def test_parse_vars(mocker):
    class Expression:
        def __init__(self, value):
            self.value = value

        def __eq__(self, other):
            return type(self) == type(other) and self.value == other.value

        def __repr__(self):
            return f"{type(self).__name__}('{self.value}')"

    class Value(Expression):
        pass

    class JinjaValue(Expression):
        pass

    class Template(Expression):
        pass

    assert Value('foo') != Template('foo')
    assert Value('foo') != Value('bar')
    assert JinjaValue('foo') != Value('foo')
    assert Template('foo') != JinjaValue('foo')

    mocker.patch('populous.vars.ValueExpression', wraps=Value)
    mocker.patch('populous.vars.JinjaValueExpression', wraps=JinjaValue)
    mocker.patch('populous.vars.TemplateExpression', wraps=Template)

    assert parse_vars(None) is None
    assert parse_vars(0) == 0
    assert parse_vars('') == ''
    assert parse_vars('foo') == 'foo'
    assert parse_vars('foo $bar') == 'foo $bar'
    assert parse_vars(' ') == ' '
    assert parse_vars(' foo ') == ' foo '
    assert parse_vars('foo') == 'foo'

    assert parse_vars('$foo') == Value('foo')
    assert parse_vars('$foo.bar') == Value('foo.bar')
    assert parse_vars('$foo.bar.lol') == Value('foo.bar.lol')
    assert parse_vars('$_a2.x3_') == Value('_a2.x3_')
    assert parse_vars('$foo  ') == Value('foo')

    assert parse_vars('$(foo)') == JinjaValue('foo')
    assert parse_vars('$(foo.bar)') == JinjaValue('foo.bar')
    assert parse_vars('$(foo.bar)') == JinjaValue('foo.bar')
    assert (
        parse_vars('$(foo|random|d("foo"))') ==
        JinjaValue('foo|random|d("foo")')
    )
    assert parse_vars('$(foo)  ') == JinjaValue('foo')

    assert parse_vars(r'\$foo') == '$foo'
    assert parse_vars(r'\$foo.bar') == '$foo.bar'
    assert parse_vars(r'\$foo.bar lol') == '$foo.bar lol'

    with pytest.raises(ValidationError):
        parse_vars('$foo bar')
    with pytest.raises(ValidationError):
        parse_vars('$1foo')
    with pytest.raises(ValidationError):
        parse_vars('$foo.2bar')
    with pytest.raises(ValidationError):
        parse_vars('$foo-bar')
    with pytest.raises(ValidationError):
        parse_vars('$foo-bar')
    with pytest.raises(ValidationError):
        parse_vars('$(foo')
    with pytest.raises(ValidationError):
        parse_vars('$foo)')
    with pytest.raises(ValidationError):
        parse_vars('$(foo).')

    assert parse_vars('{{ foo }}') == Template('{{ foo }}')
    assert parse_vars('{{ foo }} bar') == Template('{{ foo }} bar')
    assert parse_vars('bar {{ foo }}') == Template('bar {{ foo }}')
    assert parse_vars('  {{ foo }}  ') == Template('  {{ foo }}  ')
    assert (
        parse_vars('{% for x in foo %}{% endfor %}') ==
        Template('{% for x in foo %}{% endfor %}')
    )


def test_value_expression():
    from populous.vars import ValueExpression

    v = ValueExpression('foo')
    assert v.evaluate(foo='bar') == 'bar'
    assert v.evaluate(foo=1) == 1
    assert v.evaluate(foo=None) is None
    assert v.evaluate(foo=[1, 2, 3]) == [1, 2, 3]

    with pytest.raises(GenerationError) as e:
        v.evaluate()
    assert "Error generating value '$foo': 'foo' is undefined" in str(e.value)

    class Val:
        None

    a = Val()
    a.b = 'foo'
    a.c = Val()
    a.c.d = 42
    assert ValueExpression('a.b').evaluate(a=a) == 'foo'
    assert ValueExpression('a.c.d').evaluate(a=a) == 42

    with pytest.raises(GenerationError) as e:
        ValueExpression('a.b').evaluate(a=42)
    msg = "Error generating value '$a.b': 'int' object has no attribute 'b'"
    assert msg in str(e.value)


def test_jinja_value_expression():
    from populous.vars import JinjaValueExpression

    v = JinjaValueExpression('foo')
    assert v.evaluate(foo='bar') == 'bar'
    assert v.evaluate(foo=1) == 1

    v = JinjaValueExpression('foo|random')
    assert v.evaluate(foo=[1, 2, 3]) in [1, 2, 3]

    v = JinjaValueExpression('foo + bar')
    assert v.evaluate(foo=41, bar=1) == 42

    v = JinjaValueExpression('foo|d("toto")')
    assert v.evaluate() == 'toto'

    v = JinjaValueExpression('foo|upper')
    with pytest.raises(GenerationError) as e:
        v.evaluate()
    msg = "Error generating value '$(foo|upper)': 'foo' is undefined"
    assert msg in str(e.value)

    class Val:
        None

    a = Val()
    a.b = 'foo'
    a.c = Val()
    a.c.d = 42
    assert JinjaValueExpression('a.b').evaluate(a=a) == 'foo'
    assert JinjaValueExpression('a.c.d').evaluate(a=a) == 42

    v = JinjaValueExpression('a.toto')
    with pytest.raises(GenerationError) as e:
        v.evaluate(a=None)
    msg = "Error generating value '$(a.toto)': 'None' has no attribute 'toto'"
    assert msg in str(e.value)

    with pytest.raises(ValidationError) as e:
        v = JinjaValueExpression('foo|')
    msg = ("Error parsing '$(foo|)': Invalid Jinja2 expression (unexpected "
           "end of template, expected 'name'.)")
    assert msg in str(e.value)


def test_template_expression():
    from populous.vars import TemplateExpression

    t = TemplateExpression('{{ foo }} bar')
    assert t.evaluate(foo='test') == 'test bar'
    assert t.evaluate(foo='$foo') == '$foo bar'
    assert t.evaluate(foo=42) == '42 bar'
    assert t.evaluate(foo=None) == 'None bar'
    assert t.evaluate(foo='') == ' bar'

    t = TemplateExpression('{{ foo }} {{ foo }}')
    assert t.evaluate(foo='test') == 'test test'

    t = TemplateExpression('{{ foo|upper }}')
    assert t.evaluate(foo='test') == 'TEST'

    class Val:
        None

    a = Val()
    a.b = 'foo'
    a.c = Val()
    a.c.d = 42
    t = TemplateExpression('{{ var.b }} - {{ var.c.d }}')
    assert t.evaluate(var=a) == 'foo - 42'

    t = TemplateExpression(
        '{% for x in range(3) %}{{ x }} {{ foo }}\n{% endfor %}'
    )
    assert t.evaluate(foo='x') == """0 x
1 x
2 x
"""

    with pytest.raises(ValidationError) as e:
        t = TemplateExpression('{{ foo')
    msg = ("Error parsing template '{{ foo': unexpected end of "
           "template, expected 'end of print statement'.")
    assert msg in str(e.value)

    t = TemplateExpression('{{ foo }}')
    with pytest.raises(GenerationError) as e:
        t.evaluate()
    msg = "Error generating template '{{ foo }}': 'foo' is undefined"
    assert msg in str(e.value)

    t = TemplateExpression('{{ foo.bar }}')
    with pytest.raises(GenerationError) as e:
        t.evaluate(foo=42)
    msg = ("Error generating template '{{ foo.bar }}': 'int object' has no "
           "attribute 'bar'")
    assert msg in str(e.value)


def test_jinja_random():
    from populous.vars import JinjaValueExpression
    from populous.vars import TemplateExpression

    j = JinjaValueExpression('[21, 42]|random')
    assert {j.evaluate() for _ in range(100)} == {21, 42}

    j = JinjaValueExpression('[]|random')
    with pytest.raises(GenerationError) as e:
        j.evaluate()
    msg = ("Error generating value '$([]|random)': No random item, sequence "
           "was empty.")
    assert msg in str(e.value)

    t = TemplateExpression('{{ [21, 42]|random }}')
    assert {t.evaluate() for _ in range(100)} == {"21", "42"}
