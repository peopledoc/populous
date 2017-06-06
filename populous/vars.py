import re
from operator import attrgetter

import jinja2

from populous.compat import basestring
from populous.exceptions import GenerationError
from populous.exceptions import ValidationError
from populous.jinja import jinja_env


VAR_REGEX = re.compile(r'^[a-zA-Z_][a-zA-Z0-9_]*(\.[a-zA-Z_][a-zA-Z0-9_]*)*$')


def parse_vars(value):
    if not value or not isinstance(value, basestring):
        return value

    if value[0] == '$':
        value = value.strip()

        # find out if it is a '$var` or `$(expr)`
        if len(value) > 1 and value[1] == '(':
            if value[-1] != ')':
                raise ValidationError(
                    "Error parsing '{}': Missing ')'".format(value)
                )
            return JinjaValueExpression(value[2:-1])

        if not VAR_REGEX.match(value[1:]):
            raise ValidationError(
                "Error parsing '{}': This is not a valid value expression. "
                "You should either escape the $ with a '\\', or use the "
                "template syntax ('... {{{{ var }}}} ...')."
                .format(value)
            )
        return ValueExpression(value[1:])
    elif value.startswith('\$'):
        # the $ was escaped, remove the escape char
        value = value[1:]

    if '{{' in value or '{%' in value:
        # this might be a template expression
        # even if it's not, using a TemplateExpression will return
        # the same result and be almost as fast
        return TemplateExpression(value)

    return value


class Expression(object):

    def evaluate(self, **vars):
        raise NotImplementedError()


class ValueExpression(Expression):

    def __init__(self, value):
        self.value = value
        self.var, _, attrs = value.partition('.')
        if attrs:
            self.attrgetter = attrgetter(attrs)
        else:
            self.attrgetter = None
        self.attrs = attrs

    def evaluate(self, **vars_):
        try:
            var = vars_[self.var]
        except KeyError:
            raise GenerationError(
                "Error generating value '${}': '{}' is undefined"
                .format(self.value, self.var)
            )
        if self.attrgetter:
            try:
                return self.attrgetter(var)
            except AttributeError as e:
                # this message is not very informative ('type' object has no
                # attribute 'attr'), but we cannot do much better without
                # inspecting the calling frame
                raise GenerationError(
                    "Error generating value '${}': {}"
                    .format(self.value, e)
                )
        else:
            return var


class JinjaValueExpression(Expression):

    def __init__(self, value):
        self.value = value
        try:
            self.expression = jinja_env.compile_expression(
                value, undefined_to_none=False
            )
        except jinja2.TemplateError as e:
            raise ValidationError(
                "Error parsing '$({})': Invalid Jinja2 expression ({})"
                .format(value, e)
            )

    def evaluate(self, **vars_):
        try:
            value = self.expression(vars_)
            if isinstance(value, jinja2.Undefined):
                # trigger a UndefinedError
                str(value)
            return value
        except jinja2.UndefinedError as e:
            raise GenerationError(
                "Error generating value '$({})': {}".format(self.value, e)
            )


class TemplateExpression(Expression):

    def __init__(self, value=""):
        self.value = value
        try:
            self.template = jinja_env.from_string(value)
        except jinja2.TemplateError as e:
            raise ValidationError(
                "Error parsing template '{}': {}"
                .format(value, e)
            )

    def evaluate(self, **vars_):
        try:
            return self.template.render(vars_)
        except jinja2.UndefinedError as e:
            raise GenerationError(
                "Error generating template '{}': {}".format(self.value, e)
            )
